import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("share").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(location.href)
    toast.success("Link copied", { description: "Anyone in the team can open it." })
  } catch {
    toast.error("Could not copy the link", { description: "Copy it from the address bar." })
  }
})

document.getElementById("invite").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(`${location.origin}/invite/web`)
    toast.success("Invite link copied", { description: "Anyone with the link can ask to join." })
  } catch {
    toast.error("Could not copy the invite link")
  }
})

document.getElementById("delete-project").addEventListener("click", () => {
  toast("Project deleted", { description: "Website redesign is in the trash for 30 days." })
})
