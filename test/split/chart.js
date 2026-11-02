import { chart, statTile } from "../../clanker-ui-chart.min.js"

const rows = [
  { month: "January", desktop: 186, mobile: 80 },
  { month: "February", desktop: 305, mobile: 200 },
  { month: "March", desktop: 237, mobile: 120 },
  { month: "April", desktop: 73, mobile: 190 },
]
chart(document.getElementById("split-chart"), { rows, config: { desktop: { label: "Desktop" }, mobile: { label: "Mobile" } } }, { type: "bar", x: "month", label: "Visitors", animate: false })
statTile(document.getElementById("split-stat"), { label: "Revenue", value: 45231, delta: 0.2 })
