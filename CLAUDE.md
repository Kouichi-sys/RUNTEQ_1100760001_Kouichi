# プロジェクト概要

製造現場の監視カメラ(NxWitness)映像を、専用PCに依存せず社内LAN上のPCからWebブラウザで確認・共有できるWebアプリ。RUNTEQ卒業制作。詳細な背景・課題整理はREADME.mdを参照。

## 技術スタック

- フレームワーク: Django
- DB: PostgreSQL
- 環境構築: Docker
- デプロイ先: 社内オンプレミス環境(社内設置サーバーPC)
- 外部連携: NxWitness API(映像データ・ブックマーク連携)

## データベース設計(4テーブル構成)

命名は中学英語レベルの平易な単語を使う方針(講師の指導に基づく)。

### users
- id (PK)
- email (string, unique) — ログインはemailのみ。社員番号(number)は使わない
- password (string)
- name (string)
- created_at / updated_at

### servers
- id (PK)
- name (string)
- address (string) — NxWitness APIの接続先
- line (string) — 対象の製造ライン名

### cameras
- id (PK)
- server_id (FK → servers) — 1台のサーバーに複数カメラが接続される(1:多)
- name (string)

### clips
- id (PK)
- user_id (FK → users)
- camera_id (FK → cameras) — server_idではなくcamera_id(カメラ単位まで特定する設計)
- title (string)
- file (string) — 実ファイルへのパス。バイナリはDBに入れない
- media_type (string) — "image" または "video"
- taken_at (datetime)
- memo (text)

**リレーション**: servers 1:多 cameras / cameras 1:多 clips / users 1:多 clips (多対多なし、STI不使用)

## ファイルストレージの方針(重要な設計判断)

- クリップ(静止画・動画)は実ファイルとして保存し、NxWitness側のデータには一切影響を与えない
- Webサーバーのローカルディスクではなく、**社内NASをネットワークドライブとしてマウントし、そこに保存する**(Djangoの`MEDIA_ROOT`をNASのマウント先に向ける)
- DBには実ファイルのパス(`clips.file`)のみを保持し、バイナリは持たない
- 過去映像の検索・再生は、NxWitness側の録画をAPI経由でその都度参照する。ユーザーが保存したいものだけを`clips`として実ファイル保存する

## MVPスコープ(README 7章・11章に準拠)

- ユーザー登録・認証(email + password、登録/ログイン/ログアウト。パスワードリセット・メール変更は対象外)
- ライブ映像閲覧(静止画ベース、通信帯域に配慮)
- 過去映像検索・再生(巻き戻し・早送り)
- クリップ保存・詳細閲覧・編集・削除(本人のクリップのみ操作可能な権限制御が必要)
- マイページ(自分の保存済みクリップ一覧)
- カメラ列(サーバー)切り替え

## 開発の進め方(Issueベース)

- GitHub Projectsで管理。1週間ごとの看板(列)にIssueを振り分け済み
- 1 Issue = 1ブランチ = 1PR
- PRの説明文に `Closes #番号` を書き、マージでIssueを自動クローズする
- mainへの直接pushは禁止。必ずPR経由

## 品質面で必須のIssue(後回しにしない)

- テストヘルパー(factory_boy)導入、主要機能のテスト
- カバレッジ測定(coverage.py)
- N+1問題の検出・解消(django-debug-toolbar等)
- Fat Controller / Fat Modelの解消
- GitHub ActionsでのCI設定

## 実装時の注意点

- NxWitness APIとの疎通確認を最優先で行う(他機能実装前に、認証方式・レスポンス形式・帯域の制約を確認済みにする)
- テーブル・カラム名は平易な英単語を使う方針を継続する(新しいテーブル・カラムを追加する際も同様)
