// Maps each form field to the preview element it should update.
// Everything here runs client-side only — the live preview never
// touches the server, so it updates instantly on every keystroke.
const FIELD_MAP = {
    'f-fullname':      { target: 'p-fullname',      type: 'text', fallback: 'Your Name' },
    'f-email':         { target: 'p-email',         type: 'text' },
    'f-phone':         { target: 'p-phone',         type: 'text' },
    'f-location':      { target: 'p-location',      type: 'text' },
    'f-linkedin':      { target: 'p-linkedin',      type: 'text' },
    'f-summary':       { target: 'p-summary',       type: 'text' },
    'f-education':     { target: 'p-education',     type: 'text' },
    'f-experience':    { target: 'p-experience',    type: 'text' },
    'f-projects':      { target: 'p-projects',      type: 'text' },
    'f-certifications':{ target: 'p-certifications',type: 'text' },
    'f-skills':        { target: 'p-skills',        type: 'skills' },
};

function renderSkills(container, rawValue) {
    const skills = rawValue.split(',').map(s => s.trim()).filter(Boolean);
    container.innerHTML = '';
    skills.forEach(skill => {
        const li = document.createElement('li');
        li.textContent = skill;
        container.appendChild(li);
    });
}

function syncField(fieldId, config) {
    const source = document.getElementById(fieldId);
    const target = document.getElementById(config.target);
    if (!source || !target) return;

    const update = () => {
        const value = source.value;
        if (config.type === 'skills') {
            renderSkills(target, value);
        } else {
            target.textContent = value || (config.fallback || '');
        }
    };

    source.addEventListener('input', update);
    update(); // populate immediately (handles edit-mode prefill too)
}

document.addEventListener('DOMContentLoaded', () => {
    Object.entries(FIELD_MAP).forEach(([fieldId, config]) => syncField(fieldId, config));
});
