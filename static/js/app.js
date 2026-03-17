/* ── MEDFUSION Client-Side JavaScript ────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    initNavToggle();
    initAnimations();
    initDiseaseAutocomplete();
});


/* ── Mobile Navigation Toggle ────────────────────────────── */
function initNavToggle() {
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle && links) {
        toggle.addEventListener('click', () => {
            links.classList.toggle('open');
        });
    }
}


/* ── Scroll Animations ───────────────────────────────────── */
function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}


/* ── Disease Autocomplete ────────────────────────────────── */
function initDiseaseAutocomplete() {
    const inputs = document.querySelectorAll('.disease-search-input');
    inputs.forEach(input => {
        let timeout;
        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-secondary, #0f1629);
            border: 1px solid var(--border-color, rgba(148,163,184,0.1));
            border-radius: 8px;
            max-height: 250px;
            overflow-y: auto;
            z-index: 50;
            display: none;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        `;

        const wrapper = input.parentElement;
        wrapper.style.position = 'relative';
        wrapper.appendChild(dropdown);

        input.addEventListener('input', () => {
            clearTimeout(timeout);
            const query = input.value.trim();
            if (query.length < 2) {
                dropdown.style.display = 'none';
                return;
            }
            timeout = setTimeout(() => fetchSuggestions(query, dropdown, input), 300);
        });

        input.addEventListener('blur', () => {
            setTimeout(() => { dropdown.style.display = 'none'; }, 200);
        });
    });
}

async function fetchSuggestions(query, dropdown, input) {
    try {
        const resp = await fetch(`/diseases/api/search?q=${encodeURIComponent(query)}`);
        const data = await resp.json();
        dropdown.innerHTML = '';

        if (data.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        data.forEach(disease => {
            const item = document.createElement('div');
            item.style.cssText = `
                padding: 10px 14px;
                cursor: pointer;
                font-size: 0.9rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: background 150ms;
            `;
            item.innerHTML = `
                <span>${disease.name}</span>
                <span style="font-family: var(--font-mono, monospace); font-size: 0.75rem; color: var(--accent-primary, #00d4ff); opacity: 0.7;">${disease.icd_code || ''}</span>
            `;
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = 'rgba(0,212,255,0.08)';
            });
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'transparent';
            });
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                input.value = disease.name;
                dropdown.style.display = 'none';
            });
            dropdown.appendChild(item);
        });
        dropdown.style.display = 'block';
    } catch (e) {
        console.error('Autocomplete error:', e);
    }
}


/* ── Chart Rendering (Chart.js helper) ───────────────────── */
function renderTimeSeriesChart(canvasId, labels, datasets, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets.map((ds, i) => ({
                label: ds.label,
                data: ds.data,
                borderColor: ds.color || ['#00d4ff', '#7c3aed', '#22c55e', '#f97316'][i % 4],
                backgroundColor: (ds.color || ['#00d4ff', '#7c3aed', '#22c55e', '#f97316'][i % 4]) + '15',
                borderWidth: 2,
                fill: ds.fill !== undefined ? ds.fill : true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4,
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: !!title,
                    text: title,
                    color: '#e2e8f0',
                    font: { size: 14, weight: '600', family: 'Inter' },
                },
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        pointStyle: 'circle',
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 22, 41, 0.95)',
                    titleColor: '#e2e8f0',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(0, 212, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    titleFont: { family: 'Inter', weight: '600' },
                    bodyFont: { family: 'Inter' },
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.05)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 }, maxTicksLimit: 12 },
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.05)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
                },
            },
        },
    });
}


function renderBarChart(canvasId, labels, data, label, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: color || '#00d4ff33',
                borderColor: color || '#00d4ff',
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 22, 41, 0.95)',
                    borderColor: 'rgba(0, 212, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.05)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
                },
            },
        },
    });
}


/* ── Number Formatting ───────────────────────────────────── */
function formatNumber(num) {
    if (num === null || num === undefined) return '—';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toLocaleString();
}
