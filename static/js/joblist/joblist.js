// Auto-hide alerts
document.addEventListener("DOMContentLoaded", function() {
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.classList.add('hide');
            setTimeout(() => alert.remove(), 600);
        });
    }, 4000);
});
