const tree = document.getElementById("file-tree-demo")

tree.addEventListener("click", event => {
  const file = event.target.closest('[data-slot="button"]:not([data-collapsible-trigger])')
  if (!file || !tree.contains(file)) return
  for (const other of tree.querySelectorAll('[aria-current="true"]')) {
    other.removeAttribute("aria-current")
    other.classList.remove("bg-accent", "text-accent-foreground")
  }
  file.setAttribute("aria-current", "true")
  file.classList.add("bg-accent", "text-accent-foreground")
})
