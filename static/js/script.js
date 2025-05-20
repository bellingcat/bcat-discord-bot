document.addEventListener("DOMContentLoaded", () => {
  fetchDiscussions();
  makeCardsClickable();
});

async function fetchDiscussions() {
  try {
    const response = await fetch("/api/discussions");
    const data = await response.json();
    renderDiscussions(data.discussions);
  } catch (error) {
    console.error("Error fetching discussions:", error);
    document.getElementById("discussions-container").innerHTML =
      '<div class="error-message">Failed to load discussions. Please try again later.</div>';
  }
}

function renderDiscussions(discussions) {
  const container = document.getElementById("discussions-container");

  if (!discussions || discussions.length === 0) {
    container.innerHTML =
      '<div class="no-discussions">No discussions found.</div>';
    return;
  }

  // Limit to only 2 discussions when in mobile/single-column view
  const isMobile = window.innerWidth <= 550;
  const displayDiscussions = isMobile ? discussions.slice(0, 2) : discussions;

  const discussionsHTML = displayDiscussions
    .map((discussion) => {
      // Create tag HTML
      const tagsHTML = discussion.tags
        .filter((tag) => tag && tag !== "None")
        .map((tag) => {
          let icon = "";

          // Customize icons based on tag names
          if (tag.includes("Tools")) {
            icon =
              '<svg class="tag-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12.32 2c2.45 0 4.73.4 6.86 1.19l.27.09.13.05c.62.28.99.92.96 1.59l-.04 1.3-.3 5.54c-.05.86-.55 1.62-1.31 1.98-1.69.79-8.08 3.57-8.08 3.57s-3.57 1.36-8.33 3.53l-.53.21C1.5 21.24 1 20.63 1 19.96l.01-15.95c0-.66.35-1.26.88-1.57l.27-.18C3.91 1.43 5.09 1.2 5.09 1.2 7.47 1 9.34 1 10.76 1c.45 0 .86 0 1.25.02l.31.02zm5.36 3.81l-.1-.04c-1.39-.51-2.93-.78-4.98-.78-.46-.01-.94-.02-1.47-.02-.89 0-1.85 0-2.87.03l-.61.03s-.66.13-1.25.37l-.18.07c-.08.03-.14.07-.21.12l-.1.07v13.77l5.98-2.56 5.82-2.58.05-.03c.05-.02.08-.05.11-.09.03-.03.05-.08.05-.13l.02-.04.27-5.09c.01-.13-.18.04-.53-.1z"/></svg>';
          } else if (tag.includes("Research")) {
            icon =
              '<svg class="tag-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.516 6.516 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5z"/></svg>';
          } else if (tag.includes("News")) {
            icon =
              '<svg class="tag-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M20 3H4c-1.1 0-1.99.9-1.99 2L2 17c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14H7v-4h4v4zm0-6H7V7h4v4zm6 6h-4v-4h4v4zm0-6h-4V7h4v4z"/></svg>';
          } else if (tag.includes("Data")) {
            icon =
              '<svg class="tag-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12 3C7.58 3 4 4.79 4 7v10c0 2.21 3.59 4 8 4s8-1.79 8-4V7c0-2.21-3.58-4-8-4zm0 2c3.87 0 6 1.5 6 2s-2.13 2-6 2-6-1.5-6-2 2.13-2 6-2zm0 14c-3.87 0-6-1.5-6-2v-1.68c1.42.75 3.59 1.29 6 1.29s4.58-.54 6-1.29V17c0 .5-2.13 2-6 2zm0-4c-3.87 0-6-1.5-6-2v-1.77c1.42.77 3.59 1.31 6 1.31s4.58-.54 6-1.31V13c0 .5-2.13 2-6 2zm0-4c-3.87 0-6-1.5-6-2V9.32c1.42.75 3.59 1.29 6 1.29s4.58-.54 6-1.29V11c0 .5-2.13 2-6 2z"/></svg>';
          } else {
            // Default tag icon
            icon =
              '<svg class="tag-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/></svg>';
          }

          return `<div class="tag">${icon}${tag}</div>`;
        })
        .join("");

      return `
            <div class="discussion-card" onclick="openDiscordChannel('${discussion.discord_url}')">
                <div class="card-content">
                    <h3 class="card-title">${discussion.title}</h3>
                    <p class="card-text">${discussion.content}</p>
                </div>
                <div class="card-footer">
                    <div class="interactions">
                        <div class="interaction">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
                            </svg>
                            ${discussion.message_count}
                        </div>
                        <div class="interaction">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16zm4-9h-3V8a1 1 0 00-2 0v3H8a1 1 0 000 2h3v3a1 1 0 002 0v-3h3a1 1 0 000-2z"/>
                            </svg>
                            ${discussion.reaction_count}
                        </div>
                    </div>
                    <div class="time-ago">${discussion.time_ago}</div>
                </div>
            </div>
        `;
    })
    .join("");

  container.innerHTML = discussionsHTML;
}

// Add event listener to handle responsive changes
window.addEventListener("resize", function () {
  fetchDiscussions();
});

// Function to open Discord channel link
function openDiscordChannel(url) {
  window.open(url, "_blank");
}

function makeCardsClickable() {
  const cards = document.querySelectorAll(".discussion-card");

  cards.forEach((card) => {
    card.addEventListener("click", function () {
      const link = this.querySelector("a").getAttribute("href");
      if (link) {
        window.open(link, "_blank");
      }
    });
  });
}
