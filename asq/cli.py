# -*- coding: utf-8 -*-
import sys
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
    default='gpt-4o-mini',
    help='使用するLLMのモデル名を指定します (例: gpt-4o, claude-3-opus)。 デフォルト: gpt-4o-mini'
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
def main(model, system, temperature, json_mode):
    """
    標準入力からプロンプトを受け取り、LLM APIに送信し、その応答を標準出力へ出力します。
    """
    # 仕様1: 標準入力 (stdin) から全てのデータを読み込み、これをユーザープロンプトとして設定する。
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

        # 仕様6: LLMからの最終応答テキストを標準出力 (stdout) へ直接出力する。
        content = response.choices[0].message.content # type: ignore
        sys.stdout.write(content) # type: ignore

    except Exception as e:
        spinner.fail(f"エラーが発生しました")
        # 仕様4 & 7: エラーは標準エラー出力（stderr）に出力し、非ゼロの終了コードで終了する。
        # APIキー未設定のエラー(AuthenticationError)もここで捕捉される。
        sys.stderr.write(f"エラー詳細: {type(e).__name__}: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
