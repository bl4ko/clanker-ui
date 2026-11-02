import { toast } from "/clanker-ui.js"

document.addEventListener("click", event => {
  if (!event.target.closest("[data-behavior-toast]")) return
  const id = toast.add({ title: "Event created", description: "Sunday, December 3 at 9:00 AM", actionProps: { children: "Undo", onClick: () => toast.close(id) } })
})
