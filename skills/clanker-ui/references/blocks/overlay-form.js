import { dialogClose, h, icon, toast } from "/vendor/clanker-ui/clanker-ui.min.js"

const reviews = document.getElementById("reviews")
const reviewForm = document.getElementById("review-form")
const bookForm = document.getElementById("book-form")
let count = 24

function stars(n) {
  return h("span", { "data-slot": "rating", role: "img", "aria-label": `${n} of 5 stars` }, ...[1, 2, 3, 4, 5].map(i => icon("star", i <= n ? { fill: "currentColor" } : {})))
}

reviewForm.addEventListener("form:submit", event => {
  event.preventDefault()
  const { rating, title, text } = event.detail.values
  count += 1
  reviews.prepend(h("div", { "data-slot": "item", role: "listitem" },
    h("div", { "data-slot": "item-media" }, h("span", { "data-slot": "avatar" }, h("span", { "data-slot": "avatar-fallback" }, "AR"))),
    h("div", { "data-slot": "item-content" },
      h("div", { "data-slot": "item-title" }, title),
      h("p", { "data-slot": "item-description" }, "Ana Rossi · ", h("time", {}, "Just now")),
      h("p", {}, text)),
    h("div", { "data-slot": "item-actions" }, stars(Number(rating)))))
  reviews.lastElementChild.remove()
  document.getElementById("review-count").textContent = `4 of ${count} reviews, newest first.`
  dialogClose("review-dialog")
  reviewForm.reset()
  toast.success("Review posted", { description: "Members see it on the book page." })
})

bookForm.addEventListener("form:submit", event => {
  event.preventDefault()
  const { title, author, year, pages, synopsis } = event.detail.values
  document.querySelector('[data-slot="page-title"]').textContent = title
  document.querySelector('[data-slot="breadcrumb-page"]').textContent = title
  document.querySelector('[data-slot="page-description"]').textContent = `${author} · ${year} · ${pages} pages. Our November pick, discussed on Nov 18.`
  document.getElementById("book-about").textContent = synopsis
  dialogClose("edit-book")
  toast.success("Details saved", { description: `${title} is up to date.` })
})

document.getElementById("rsvp").addEventListener("click", () => {
  toast.success("See you on Nov 18", { description: "Café Moro at 19:00. We sent you a calendar invite." })
})
