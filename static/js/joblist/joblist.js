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
updateClock();

// Search Filter
function filterJobs() {
    const q = document.getElementById('searchInput').value.toLowerCase();
    document.querySelectorAll('.card').forEach(card => {
        const title = card.querySelector('h3').innerText.toLowerCase();
        card.style.display = title.includes(q) ? '' : 'none';
    });
}

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
