import { toast } from "../../clanker-ui-overlays.min.js"

toast.success("Event created", { description: "Sunday, December 3", duration: Infinity })
toast("Saved", { duration: Infinity, action: { label: "Undo", onClick() {} } })
