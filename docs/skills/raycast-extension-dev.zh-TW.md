# raycast-extension-dev

用 TypeScript 開發、驗證並上架 [Raycast](https://developers.raycast.com/) 擴充。
Raycast 官方文件已經寫清楚 `List` 和 `Form` 收什麼參數；這個 skill 負責另外那 20% ——
**工具鏈不會檢查的、runtime 不會提供的，以及 store 會檢查但 linter 不會的**。

裡面每一條都是開發
[Pueue for Raycast](https://github.com/daviddwlee84/Pueue-Raycast-Extension)
時真的踩過一次才寫下來的，多數可以追回該 repo 的
[`pitfalls/`](https://github.com/daviddwlee84/Pueue-Raycast-Extension/tree/main/pitfalls)。

| 介面 | 回答什麼問題 |
|---|---|
| `new-raycast-extension.sh` | 「幫我 scaffold 一個從第一個 commit 就有 gate 的擴充。」 |
| `check-store-readiness.sh` | 「`ray lint` 剛剛過了，但 store 審核會退什麼？」 |
| [`references/runtime-and-subprocess.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/runtime-and-subprocess.md) | 「terminal 裡 `which` 秒找到，為什麼擴充說找不到？」 |
| [`references/manifest-and-commands.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/manifest-and-commands.md) | 「`package.json` 的 command / preference / argument 到底能寫什麼？」 |
| [`references/data-and-state.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/data-and-state.md) | 「為什麼我的動作閃一下、跳回去、然後又生效？」 |
| [`references/ui-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/ui-patterns.md) | 「該用哪個 List/Form/ActionPanel 慣用法？dropdown 為什麼自己重設了？」 |
| [`references/menu-bar.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/menu-bar.md) | 「不開 Raycast 怎麼顯示一個數字？為什麼我的是舊的？」 |
| [`references/store-publishing.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/store-publishing.md) | 「上架前還差什麼？哪些永遠自動化不了？」 |

## 為什麼 gate 是四個指令

Raycast 工具鏈最貴的一個事實：

| 指令 | 抓得到 | 抓不到 |
|---|---|---|
| `tsc --noEmit` | 型別 | manifest、格式、runtime 形狀 |
| `node dev-check.js` | 你自己的不變式、wire shape、產生出來的 argv | 你沒斷言的一切 |
| `ray lint` | manifest schema、icon、ESLint、Prettier、保留快捷鍵衝突 | 型別 |
| `ray build`（`-e dev`） | 語法、esbuild 打得包起來 | **型別 —— esbuild 只剝掉型別，不檢查** |
| `ray build -e dist` | 以上再加**型別**（它會跑 `tsc -p tsconfig.json --noEmit`） | manifest、格式 |

用一個帶有真實 `TS2345` 的 scaffold 實測：`ray build` exit **0** 並印出
`ready - built extension successfully`；`ray build -e dist` exit **1** 並回報錯誤。
所以 dist build 其實比多數人以為的更嚴格 —— 但 `npm run build`、`just build`、
`ray develop` 全都是 *dev* build，這正是型別錯誤能一路活到上線的原因。

來源擴充有兩個真實 bug 走的就是這條路：把 `MutatePromise<GroupMap>` 傳給預期
`MutatePromise<State>` 的地方（runtime 會在每次操作後把清單清空），以及
`@raycast/api` 自帶一份 `@types/react` 造成的 `ReactNode`/`JSX.Element` 衝突。
兩個都沒有印出任何一行訊息。

這個 gate 以 `assets/Justfile.template` 提供，scaffolder 會寫進每個新擴充。

## `ray lint` 不檢查什麼

實測而非推測：**`metadata/` 完全空的時候 `ray lint` 仍然 exit 0**，
連 "validate extension metadata" 那一階段都是綠的。所以 linter 不能當上架關卡 ——
截圖數量與尺寸、icon 尺寸、icon 是不是還是 placeholder、CHANGELOG 佔位符、
`author` 是不是真的帳號，全都是本機沒有任何東西會跑的審核期需求。

`check-store-readiness.sh` 就是補這一欄，輸出
`{id, status, detail, fix}` 的 JSON 陣列，失敗時 exit `4`，
因為缺工具而略過某項檢查時 exit `3`（略過永遠不會被當成通過）。

## 什麼時候會觸發

- 「幫我做一個 X 的 Raycast 擴充」／「把這個 CLI 包成 Raycast」
- 「`npm run dev` 可以，從 Raycast 開就不行」—— launchd 的 PATH 陷阱，
  而 dev console 在結構上就重現不出來
- 「menu bar 數字不對／空的／是舊的」
- 「動作閃一下、跳回去、然後又生效」
- 「把這個弄到可以上架」

## 什麼時候不該用

- **Raycast Script Commands** —— 不同 repo，沒有 manifest，也沒有 React。
- **一般 React/TSX 品質** → `react-best-practices`。
- **被包的那個 CLI 本身的語意** → 該工具自己的 skill，或它的 `--help`。
- **沒有 Raycast Pro 的 AI Extensions** —— `tools[]` 需要 Pro，而且 tool call
  裡面沒有相當於 `confirmAlert` 的確認介面，所以第一版只能是唯讀的。
- **實際去截圖。** 這個 skill 能驗證數量和尺寸，但它截不了視窗 —— 任何 CLI 都不行。

## 結構

```text
skills/local/raycast-extension-dev/
├── SKILL.md                              485 行 —— workflow A-F 與 27 條 gotcha
├── references/
│   ├── runtime-and-subprocess.md         launchd 環境、路徑探測、execFile、串流、錯誤分類
│   ├── manifest-and-commands.md          所有 manifest 欄位 + schema 長度下限
│   ├── data-and-state.md                 hooks、cache key 作用域、reconcile 量測流程
│   ├── ui-patterns.md                    List/Detail/Form/ActionPanel、dropdown、快捷鍵、markdown 圍籬
│   ├── menu-bar.md                       每一條 MenuBarExtra 限制與其後果
│   └── store-publishing.md               檢查清單、截圖機制、審核標準
├── scripts/
│   ├── new-raycast-extension.sh          scaffold 一個帶 gate 的擴充（exit 0/1/2/3/4）
│   └── check-store-readiness.sh          ray lint 跳過的 store 檢查（exit 0/1/2/3/4）
└── assets/
    ├── Justfile.template                 四階段 gate
    ├── tsconfig.json.template            重點：include 必須列出 raycast-env.d.ts
    ├── eslint.config.mjs.template        @raycast/eslint-config v2 的 flat config
    ├── package.json.template             manifest 骨架與已知可用的依賴組合
    ├── dev-check.ts.template             沒有 test runner 的驗證骨架
    ├── transport.ts.template             Mutation data-union 接縫
    ├── error-descriptor.tsx.template     一個 descriptor、四個 renderer
    ├── metadata-README.md.template       讓「Save to Metadata」選項出現
    └── extension-icon.placeholder.png    512x512 —— 它的 sha256 就是自己的絆線
```

## Skill 主張的三件事

**把 mutation 建模成 data union，不是 argv 字串。** 一個每種操作一個 variant 的
`Mutation` 型別，才是讓 transport 成為可抽換接縫的原因。如果 `mutate()` 收的是
`string[]` argv，socket 或 HTTP transport 就得把 argv 反解回意圖 ——
那不是接縫，那是一層 shell。

**這裡沒有 test runner，加一個只會變成 store 審核的雜訊。** 讓所有純模組都不 import
`@raycast/api`，然後用一支 `dev-check.ts` 斷言它們，靠已經裝好的 `tsc` 編譯、用
`node` 執行。那條 import 紀律就是全部的前提 —— 一個會拉進 transport 的 barrel
就會把 `@raycast/api` 一起拉進來，然後什麼都不能斷言了。

**一個 error descriptor、N 個 renderer。** `structural` 旗標決定快取資料只是「舊了一下」
還是「一個沒人連得上的系統的快照」；action 保持成資料而不是 JSX，這樣
menu bar（它沒辦法 render `List.EmptyView`）可以自己映射成它的原語，
而不是長出第二份會漂移的複製品。

## 驗證方式

這個 skill 是對著真的工具鏈做出來的，不是照文件寫的：

```bash
# scaffold，然後對結果跑完整個 gate
bash scripts/new-raycast-extension.sh --dir /tmp/trial --name trial --author me \
  --command tasks:view --command queue-menu:menu-bar --command quick:no-view
cd /tmp/trial && npm install
npx ray build && npx tsc --noEmit && npx ray lint    # 三個都 exit 0
```

以及 skill 立論所依據的那一點，可重現：

```bash
npx ray lint;                              echo $?   # 0 —— 而 metadata/ 是空的
bash scripts/check-store-readiness.sh .;   echo $?   # 4 —— 而且指名缺截圖
```

補上三張正確尺寸的 PNG 之後，失敗清單剛好少一項，而且仍然報
`icon-not-placeholder` —— 這才知道檢查器是在判斷，而不是單純數檔案。

正式來源是
[`SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/SKILL.md)。
