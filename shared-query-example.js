(() => {
  'use strict';

  const lab = document.querySelector('[data-shared-query-lab]');
  if (!lab) return;

  const rootTwo = Math.sqrt(2);
  const keys = [[1, 0], [0, 1]];
  const values = [[2, 0], [0, 2]];
  const queries = {
    a: { label: 'Query A', vector: [rootTwo, 0] },
    b: { label: 'Query B', vector: [0, rootTwo] }
  };

  const one = (name) => lab.querySelector(`[data-shared-query-${name}]`);
  const reveal = one('reveal');
  const work = one('work');
  const takeaway = one('takeaway');
  const feedback = one('feedback');
  const controls = one('controls');
  let prediction = null;
  let revealed = false;

  const dot = (left, right) => left.reduce((sum, value, index) => sum + value * right[index], 0);
  const scale = (vector, divisor) => vector.map((value) => value / divisor);
  const weightedSum = (weights, vectors) => vectors[0].map((_, index) => weights.reduce((sum, weight, row) => sum + weight * vectors[row][index], 0));
  const softmax = (scores) => {
    const exponentials = scores.map((score) => Math.exp(score));
    const total = exponentials.reduce((sum, value) => sum + value, 0);
    return exponentials.map((value) => value / total);
  };
  const rounded = (value) => Math.abs(value) < 1e-10 ? '0' : value.toFixed(3).replace(/\.000$/, '');
  const exact = (value) => Math.abs(value - rootTwo) < 1e-10 ? '√2' : rounded(value);
  const vectorText = (vector, formatter = rounded) => `[${vector.map(formatter).join(', ')}]`;

  function showQuery(name) {
    const query = queries[name];
    const rawScores = keys.map((key) => dot(query.vector, key));
    const scaledScores = scale(rawScores, rootTwo);
    const weights = softmax(scaledScores);
    const output = weightedSum(weights, values);
    const queryText = vectorText(query.vector, exact);
    const rawText = vectorText(rawScores, exact);
    const scaledText = vectorText(scaledScores);
    const weightText = vectorText(weights);
    const outputText = vectorText(output);
    one('current').textContent = `${query.label} = ${queryText}`;
    one('dots').textContent = `${queryText} · Kᵀ = ${rawText}`;
    one('scaled').textContent = `${rawText} / √2 = ${scaledText}`;
    one('softmax').textContent = `softmax(${scaledText}) = ${weightText}`;
    one('output').textContent = `${rounded(weights[0])}[2, 0] + ${rounded(weights[1])}[0, 2] = ${outputText}`;
    one('result').textContent = outputText;
    lab.querySelectorAll('[data-shared-query-choice]').forEach((button) => {
      const selected = button.dataset.sharedQueryChoice === name;
      button.setAttribute('aria-pressed', String(selected));
      button.classList.toggle('selected', selected);
    });
  }

  lab.querySelectorAll('[data-shared-query-predict]').forEach((button) => {
    button.addEventListener('click', () => {
      prediction = button.dataset.sharedQueryPredict;
      lab.querySelectorAll('[data-shared-query-predict]').forEach((choice) => {
        const selected = choice === button;
        choice.setAttribute('aria-pressed', String(selected));
        choice.classList.toggle('selected', selected);
      });
      reveal.disabled = false;
      feedback.textContent = 'Prediction saved. Reveal the calculation to check it.';
    });
  });

  reveal.addEventListener('click', () => {
    revealed = true;
    showQuery('a');
    work.hidden = false;
    takeaway.hidden = false;
    controls.hidden = false;
    feedback.textContent = prediction === 'first'
      ? 'Correct: Query A gives the first coordinate more weight.'
      : 'Close: Query A scores the first key higher, so the first coordinate is larger.';
    feedback.classList.add('success');
    reveal.textContent = 'Calculation revealed';
  });

  lab.querySelectorAll('[data-shared-query-choice]').forEach((button) => {
    button.addEventListener('click', () => {
      showQuery(button.dataset.sharedQueryChoice);
      if (revealed) feedback.textContent = 'The fixed K and V did not change. Only the query changed.';
    });
  });

  showQuery('a');
})();
