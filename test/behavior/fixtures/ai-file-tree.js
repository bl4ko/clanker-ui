const tree = document.getElementById("file-tree-demo")

tree.addEventListener("click", event => {
  const file = event.target.closest('[data-slot="button"]:not([data-collapsible-trigger])')
  if (!file || !tree.contains(file)) return
  for (const other of tree.querySelectorAll('[aria-current="true"]')) {
    other.removeAttribute("aria-current")
    other.dataset.behavior = "ai-tree-item"
  }
  file.setAttribute("aria-current", "true")
  file.dataset.behavior = "ai-tree-item ai-tree-current"
})
