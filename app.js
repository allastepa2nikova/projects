const catalog = [
  {
    topic: 'IT и программирование',
    items: [
      { title: 'Когда баг становится фичей', format: 'Мем', absurdity: 2, description: 'Классическая шутка про «не трогай — работает».' },
      { title: 'Junior vs Production в пятницу', format: 'Видео', absurdity: 4, description: 'Скетч о деплое за 5 минут до выходных.' },
      { title: 'Заметки линтера', format: 'Комикс', absurdity: 3, description: 'Комикс о том, как линтер обсуждает твой стиль.' }
    ]
  },
  {
    topic: 'Коты и животные',
    items: [
      { title: 'Кот-инспектор пакетов', format: 'Видео', absurdity: 3, description: 'Кот проверяет каждую коробку как таможенник.' },
      { title: 'Пёс и огурец', format: 'Мем', absurdity: 4, description: 'Неловкая реакция на самый обычный огурец.' },
      { title: 'Попугай-стендапер', format: 'Шутка', absurdity: 5, description: 'Сценка с птицей, которая перебивает ведущего.' }
    ]
  },
  {
    topic: 'Офис и работа',
    items: [
      { title: 'Созвон, который мог быть письмом', format: 'Мем', absurdity: 2, description: 'Тонкая боль всех офисных сотрудников.' },
      { title: 'Кофе до и после дедлайна', format: 'Комикс', absurdity: 3, description: '2 панели, 2 состояния, 0 спокойствия.' },
      { title: 'Фраза «быстренький вопрос»', format: 'Шутка', absurdity: 1, description: 'Шутка о самом длинном «быстреньком» диалоге.' }
    ]
  },
  {
    topic: 'Игры и гики',
    items: [
      { title: 'Лутбокс ожидание/реальность', format: 'Мем', absurdity: 3, description: 'Открываешь легендарный ящик, получаешь носки.' },
      { title: 'NPC с экзистенциальным кризисом', format: 'Видео', absurdity: 5, description: 'Скетч, где NPC задаёт слишком глубокие вопросы.' },
      { title: 'Босс на 1 HP', format: 'Шутка', absurdity: 2, description: 'Короткая история о дрожащих руках и судьбе.' }
    ]
  }
];

const topicSelect = document.querySelector('#topicSelect');
const formatSelect = document.querySelector('#formatSelect');
const absurdityRange = document.querySelector('#absurdityRange');
const pickBtn = document.querySelector('#pickBtn');
const result = document.querySelector('#result');
const topics = document.querySelector('#topics');

function init() {
  topicSelect.innerHTML = '<option value="all">Все тематики</option>' +
    catalog.map(({ topic }) => `<option value="${topic}">${topic}</option>`).join('');

  topics.innerHTML = catalog.map(({ topic }) => `<span class="chip">${topic}</span>`).join('');
}

function pickContent() {
  const selectedTopic = topicSelect.value;
  const selectedFormat = formatSelect.value;
  const selectedAbsurdity = Number(absurdityRange.value);

  const pool = catalog
    .filter(({ topic }) => selectedTopic === 'all' || topic === selectedTopic)
    .flatMap(({ topic, items }) => items.map((item) => ({ ...item, topic })))
    .filter((item) => selectedFormat === 'all' || item.format === selectedFormat)
    .sort((a, b) => Math.abs(a.absurdity - selectedAbsurdity) - Math.abs(b.absurdity - selectedAbsurdity));

  if (!pool.length) {
    result.classList.remove('empty');
    result.innerHTML = `
      <h2>Ничего не найдено 🤷</h2>
      <p>Попробуй ослабить фильтры или выбрать другой формат.</p>
    `;
    return;
  }

  const choice = pool[Math.floor(Math.random() * Math.min(3, pool.length))];

  result.classList.remove('empty');
  result.innerHTML = `
    <h2>Твоя рекомендация</h2>
    <h3>${choice.title}</h3>
    <p>${choice.description}</p>
    <div class="badges">
      <span class="badge">${choice.topic}</span>
      <span class="badge">${choice.format}</span>
      <span class="badge">Абсурд: ${choice.absurdity}/5</span>
    </div>
  `;
}

pickBtn.addEventListener('click', pickContent);
init();
