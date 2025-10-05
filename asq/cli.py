# -*- coding: utf-8 -*-
import sys
import os
import click
import litellm
from halo import Halo

# LiteLLMのデバッグ情報を非表示にする
litellm.suppress_debug_info = True

# --list オプションが指定されたときに呼び出されるコールバック関数
def show_models_and_exit(ctx, param, value):
    # -l または --list が指定されていない場合は何もしない
    if not value or ctx.resilient_parsing:
        return
    # litellm.model_list をアルファベット順にソートして標準出力に表示する
    for model in sorted(litellm.model_list):
        click.echo(model)
    # プログラムを終了する
    ctx.exit()

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option(
    '-l', '--list',
    is_flag=True,
    callback=show_models_and_exit,
    expose_value=False,
    is_eager=True, # 他のオプションより先に評価する
    help='litellmが扱えるモデル名の一覧を表示します。'
)
@click.option(
    '-m', '--model',
    # デフォルトのモデルを 'gemini/gemini-2.5-pro' に変更
    default='gemini/gemini-2.5-pro',
    # 環境変数 ASQ_MODEL を使ってモデルを指定できるようにする
    # 優先順位は click によって以下のように処理される:
    # 1. --model オプション
    # 2. ASQ_MODEL 環境変数
    # 3. default 値
    envvar='ASQ_MODEL',
    help='使用するLLMのモデル名を指定します。ASQ_MODEL環境変数でも設定可能です。デフォルト: gemini/gemini-2.5-pro'
)
@click.option(
    '-s', '--system',
    default=None,
    help='LLMに渡すシステムプロンプトを指定します。'
)
@click.option(
    '-t', '--temperature',
    type=click.FloatRange(0.0, 2.0),
    default=0.7,
    help='サンプリング温度を指定します (0.0から2.0)。 デフォルト: 0.7'
)
@click.option(
    '-j', '--json', 'json_mode',
    is_flag=True,
    default=False,
    help='モデルに応答をJSON形式で強制させます。'
)
@click.option(
    '-p', '--promp', 'promp_mode',
    is_flag=True,
    default=False,
    help='プロンプ連携モード'
)
def main(model, system, temperature, json_mode, promp_mode):
    """
    標準入力からプロンプトを受け取り、LLM APIに送信し、その応答を標準出力へ出力します。
    """
    # promp連携モード用の変数を初期化
    user_prompt = ""
    in_file_path = "" # 出力ファイルパス

    if promp_mode:
        # プロンプ連携モードが有効な場合の処理
        promp_out_dir = ".promp-out"
        promp_in_dir = ".promp-in"

        try:
            # .promp-out フォルダの存在を確認
            if not os.path.isdir(promp_out_dir):
                raise FileNotFoundError(f"入力フォルダ '{promp_out_dir}' が見つかりません。")

            # .promp-out フォルダから 'out-*.txt' 形式のファイルを探す
            out_files = [f for f in os.listdir(promp_out_dir) if f.startswith('out-') and f.endswith('.txt')]
            if not out_files:
                raise FileNotFoundError(f"'{promp_out_dir}' 内に 'out-*.txt' 形式のファイルが見つかりません。")

            # ファイル名でソートして最新のファイルを取得
            latest_out_file = max(out_files)
            latest_out_file_path = os.path.join(promp_out_dir, latest_out_file)

            # 最新ファイルの内容をプロンプトとして読み込む
            with open(latest_out_file_path, 'r', encoding='utf-8') as f:
                user_prompt = f.read()

            # 入力ファイルのタイムスタンプから出力ファイル名を生成
            timestamp = latest_out_file.replace('out-', '').replace('.txt', '')
            in_file_name = f"in-{timestamp}.txt"
            in_file_path = os.path.join(promp_in_dir, in_file_name)

            # .promp-in フォルダが存在しない場合は作成
            os.makedirs(promp_in_dir, exist_ok=True)
        except Exception as e:
            # promp連携モードでのエラー処理
            sys.stderr.write(f"エラー: {e}\n")
            sys.exit(1)
    else:
        # 通常モードの場合、標準入力からプロンプトを読み込む
        user_prompt = sys.stdin.read()

    # LLMに渡すメッセージを構築
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_prompt})

    # 仕様3: モデル、システムプロンプト、温度、JSONモードの指定はオプションで行う。
    params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,  # 仕様6: ストリーミングは行わない
    }
    if json_mode:
        params["response_format"] = {"type": "json_object"}

    # 仕様5: LLMからの回答を待っている間は、スピナーで待ち状態を表現する。
    spinner = Halo(text='LLMからの応答を待っています...', spinner='dots')

    try:
        spinner.start()
        # 仕様2: LiteLLMライブラリを用いてAPIリクエストを行う。
        response = litellm.completion(**params)
        spinner.succeed('応答を取得しました')

        # LLMからの最終応答テキストを取得
        content = response.choices[0].message.content # type: ignore

        if promp_mode:
            # プロンプ連携モードの場合、結果をファイルに書き込む
            with open(in_file_path, 'w', encoding='utf-8') as f:
                f.write(content) # type: ignore
        else:
            # 通常モードの場合、結果を標準出力に出力する
            sys.stdout.write(content) # type: ignore

    except Exception as e:
        spinner.fail(f"エラーが発生しました")
        # 仕様4 & 7: エラーは標準エラー出力（stderr）に出力し、非ゼロの終了コードで終了する。
        # APIキー未設定のエラー(AuthenticationError)もここで捕捉される。
        sys.stderr.write(f"エラー詳細: {type(e).__name__}: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
