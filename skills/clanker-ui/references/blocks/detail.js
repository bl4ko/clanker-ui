import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("share").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(location.href)
    toast.success("Link copied", { description: "Anyone in the team can open it." })
  } catch {
    toast.error("Could not copy the link", { description: "Copy it from the address bar." })
  }
})

document.getElementById("invite").addEventListener("click", () => toast("Invite sent", { description: "We sent an email to the new member." }))

document.getElementById("delete-project").addEventListener("click", () => {
  toast("Project moved to the trash", { description: "It is deleted after 30 days.", action: { label: "Undo", onClick() {} } })
})
