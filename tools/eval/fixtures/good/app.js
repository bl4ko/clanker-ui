import { toast } from "/vendor/clanker-ui/clanker-ui.min.js"

document.getElementById("profile-form").addEventListener("form:submit", event => {
  event.preventDefault()
  toast.success("Profile saved")
})
