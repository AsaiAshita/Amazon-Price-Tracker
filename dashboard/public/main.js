export async function loadElements() {
  const res = await fetch('/elements');
  if (!res.ok) throw new Error('Failed to fetch elements');
  return await res.json();
}

export function renderElements(data, titleListEl, priceListEl) {
  titleListEl.innerHTML = '';

  data.forEach(item => {
    const li = document.createElement('li');
    li.dataset.id = item.id;
    li.textContent = item.title;
    li.dataset.lowestPrice = item.lowest_price;
    li.dataset.link = item.link;
    li.dataset.image = item.image_link;
    li.dataset.date = item.date;
    titleListEl.appendChild(li);
  });

  titleListEl.onclick = async (e) => {
    if (e.target.tagName === 'LI') {
      titleListEl.querySelectorAll('li').forEach(li =>
        li.classList.remove('selected')
      );

      e.target.classList.add('selected');

      const price = e.target.dataset.lowestPrice;
      const imgSrc = e.target.dataset.image;
      const date = e.target.dataset.date;
      const title = e.target.textContent;

      priceListEl.innerHTML = `

<div style="
  background-color:#ff9d00;
  width:100%;
  height:80px;
  display:flex;
  align-items:center;
  padding:0 20px;
  box-sizing:border-box;
">

  <h2 style="
    margin:0;
    overflow:hidden;
    white-space:nowrap;
    text-overflow:ellipsis;
  ">
    ${title}
  </h2>

</div>


<div style="
  padding:20px;
  display:flex;
  align-items:center;
  gap:30px;
">
    <div style="
        width:200px;
        height:200px;
        display:flex;
        align-items:center;
        justify-content:center;
        flex-shrink:0;
    ">

      <img
        src="${imgSrc}"
        style="
          max-width:100%;
          max-height:100%;
          object-fit:contain;
        "
      >

    </div>


    <div>
      <h3 style="
      font-size: 20px">LOWEST PRICE</h3>

      <div style="
        font-size:40px;
        font-weight:bold;
        color:green;
      ">
        €${price}
      </div>

      <p>
        Reached on:
        <br>
        ${date}
      </p>
    </div>
  </div>
  
<div style="display:flex; justify-content:center; width:100%;">
  <canvas id="priceChart" style="margin-top:30px; height:200px; width:100%; max-width:800px;"></canvas>
</div>
`;
      const li = e.target.closest('li');
      const id = li.dataset.id;

      const res = await fetch(`/history/${id}`);
      const history = await res.json();

      const labels = history.map(h =>
        new Date(h.timestamp).toLocaleDateString()
      );

      const prices = history.map(h => h.price);

      // destroy old chart if exists
      if (window.priceChartInstance) {
        window.priceChartInstance.destroy();
      }

      const ctx = document.getElementById('priceChart');

      window.priceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Price history',
            data: prices,
            borderColor: '#007BFF',
            backgroundColor: 'rgba(0,123,255,0.1)',
            tension: 0.2,
            fill: true
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: true }
          },
          scales: {
            y: {
              beginAtZero: false
            }
          }
        }
      });
    }
  };
}

document.addEventListener('DOMContentLoaded', async () => {
  const titleListEl = document.getElementById('title-list');
  const priceListEl = document.getElementById('price-list');

  try {
    const data = await loadElements();
    renderElements(data, titleListEl, priceListEl);

    if (data.length > 0) titleListEl.querySelector('li').click();
  } catch (err) {
    console.error(err);
    titleListEl.innerHTML = '<li>Error loading data</li>';
  }
});
