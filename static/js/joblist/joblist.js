// Auto-hide alerts
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.classList.add('hide');
            setTimeout(() => alert.remove(), 600);
        });
    }, 50000);
});

// Clock
function updateClock() {
    const now = new Date();
    const dateEl = document.getElementById('current-date');
    const timeEl = document.getElementById('current-time');

    if (dateEl && timeEl) {
        dateEl.innerText = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        timeEl.innerText = now.toLocaleTimeString();
    }
}
setInterval(updateClock, 1000);
updateClock();// Filter jobs by search text and category

function filterJobs() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const selectedType = document.getElementById('filterSelect').value;
    const cards = document.querySelectorAll('.job-card');

    cards.forEach(card => {
        const title = card.querySelector('h3').innerText.toLowerCase();
        const desc = card.querySelector('p.text-gray-600')?.innerText.toLowerCase() || '';
        const jobType = card.getAttribute('data-type') || '';

        // Match search query
        const matchesSearch = title.includes(searchQuery) || desc.includes(searchQuery);

        // Match selected filter: All Types or matching type
        const matchesFilter = selectedType === "" || selectedType === jobType;

        card.style.display = (matchesSearch && matchesFilter) ? "" : "none";
    });
}

// Add event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('searchInput').addEventListener('input', filterJobs);
    document.getElementById('filterSelect').addEventListener('change', filterJobs);
});


// Chart (wait for DOM)
document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('analyticsChart');
    if (ctx && typeof Chart !== 'undefined' && counts) {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Users', 'Jobs', 'Applications'],
                datasets: [{
                    label: 'Platform Data',
                    data: [counts.users, counts.jobs, counts.applications],
                    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B'],
                    borderRadius: 6
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

    // Calendar
    const calendarEl = document.getElementById('jobCalendar');
    if (calendarEl && typeof FullCalendar !== 'undefined' && jobData) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            height: 350,
            events: jobData
        });
        calendar.render();
    }
});
