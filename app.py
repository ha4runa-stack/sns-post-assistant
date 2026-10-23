import json
from pathlib import Path

import streamlit as st

# 商品カテゴリの選択肢
CATEGORIES = ["美容液", "化粧水", "クリーム", "パック", "コスメ", "ヘアー", "健康", "その他"]

# JSONファイルの場所（どちらも app.py と同じフォルダにある）
TEMPLATES_PATH = Path(__file__).parent / "templates.json"
HASHTAGS_PATH = Path(__file__).parent / "hashtags.json"


def load_json(path):
    """JSONファイルを読み込んで、中身を辞書（「名前: 値」の組の集まり）として返す"""
    # encoding="utf-8" を付けないと、Windows では日本語が文字化けすることがある
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def get_hashtags(hashtags, category):
    """カテゴリに合ったハッシュタグ候補のリストを返す

    「その他」など、categories に登録されていないカテゴリは、共通のタグだけになる
    """
    category_tags = hashtags["categories"].get(category, [])
    return category_tags + hashtags["共通"]


def create_post(post_lines, inputs):
    """テンプレートの各行に入力内容を当てはめて、投稿文を作る

    post_lines: テンプレートの行のリスト（例：{"key": "scent", "text": "🌸 香り：{scent}"}）
    inputs: 入力内容の辞書（例：{"scent": "ローズの香り"}）
    """
    lines = []
    for line in post_lines:
        value = inputs[line["key"]]
        # 入力されていない項目の行は、投稿文に含めない
        if value == "":
            continue
        # {scent} のような目印の部分を、入力された文字に置きかえる
        lines.append(line["text"].replace("{" + line["key"] + "}", value))
    # 行と行を改行でつなげて、1つの文章にする
    return "\n".join(lines)


st.title("SNS投稿文作成アシスタント")

# ---- 商品情報の入力 ----
st.header("商品情報")
# strip() で前後の空白を取りのぞく（スペースだけの入力を「空欄」として扱うため）
product_name = st.text_input("商品名（必須）").strip()
brand_name = st.text_input("ブランド名").strip()
category = st.selectbox("商品カテゴリ", CATEGORIES)

# ---- 使用感の入力 ----
st.header("使用感")
texture = st.text_area("テクスチャ").strip()
scent = st.text_area("香り").strip()
usability = st.text_area("使いやすさ").strip()

# ---- お気に入りポイントの入力 ----
st.header("お気に入りポイント・商品の特徴")
favorite_points = st.text_area("お気に入りポイント・商品の特徴").strip()

# ---- 作成ボタン ----
if st.button("投稿文を作成"):
    # 前に作った投稿文を消しておく（空欄やエラーのときに、古い投稿文が残らないようにする）
    st.session_state.pop("edited_post", None)
    st.session_state.pop("hashtags", None)

    if product_name == "":
        # 商品名が空欄のときは注意メッセージを出して、先に進まない
        st.warning("商品名を入力してください。")
    else:
        try:
            templates = load_json(TEMPLATES_PATH)
            hashtags = load_json(HASHTAGS_PATH)
            inputs = {
                "product_name": product_name,
                "brand_name": brand_name,
                "texture": texture,
                "scent": scent,
                "usability": usability,
                "favorite_points": favorite_points,
            }
            post = create_post(templates["post_lines"], inputs)
            hashtag_list = get_hashtags(hashtags, category)
        except FileNotFoundError as error:
            # error.filename に、見つからなかったファイルの場所が入っている
            st.error(f"ファイルが見つかりません：{error.filename}　app.py と同じフォルダにあるか確認してください。")
        except json.JSONDecodeError as error:
            # error.lineno に、誤りが見つかった行の番号が入っている
            st.error(f"templates.json か hashtags.json の書き方に誤りがあります（{error.lineno}行目付近）。カンマ（,）や {{ }} の閉じ忘れがないか確認してください。")
        except KeyError as error:
            st.error(f"templates.json か hashtags.json の項目名に誤りがあります（{error}）。綴りを確認してください。")
        else:
            # session_state（画面を操作しても消えない保管場所）に投稿文を入れる
            # key が "edited_post" の入力欄に、この文章が表示される
            st.session_state["edited_post"] = post
            st.session_state["hashtags"] = hashtag_list

# ---- 投稿文の編集とコピー ----
# 投稿文が作られているときだけ表示する
if "edited_post" in st.session_state:
    st.subheader("作成した投稿文")
    # key を指定すると、入力欄の内容が st.session_state["edited_post"] に保存される
    edited_post = st.text_area("自由に編集できます", key="edited_post", height=250)

    st.subheader("コピー用")
    if edited_post.strip() == "":
        st.info("投稿文が空です。")
    else:
        st.caption("右上のボタンを押すと、投稿文をコピーできます。")
        # st.code の枠には、コピーボタンが付いている
        # language=None で色付けをなくし、wrap_lines=True で長い行を折り返す
        st.code(edited_post, language=None, wrap_lines=True)

    # ---- ハッシュタグ候補の表示 ----
    st.subheader("ハッシュタグ候補")
    if st.session_state["hashtags"] == []:
        st.info("ハッシュタグ候補がありません。")
    else:
        # タグをスペースでつなげて表示する（投稿文には自動で追加しない）
        st.code(" ".join(st.session_state["hashtags"]), language=None, wrap_lines=True)
