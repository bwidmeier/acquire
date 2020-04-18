// DOM elements
const gameList = document.querySelector('.game-list');
const gameBoard = document.querySelector('.game-board');
const loggedOutLinks = document.querySelectorAll('.logged-out');
const loggedInLinks = document.querySelectorAll('.logged-in');;

const setupUI = (user) => {
  if (user) {
    // toggle user UI elements
    loggedInLinks.forEach(item => item.style.display = 'block');
    loggedOutLinks.forEach(item => item.style.display = 'none');
  } else {
    // toggle user elements
    loggedInLinks.forEach(item => item.style.display = 'none');
    loggedOutLinks.forEach(item => item.style.display = 'block');
  }
};

// initialize game board
const initGameboard = (game) => {
  gameList.style.display = 'none';
  gameBoard.style.display = 'block';

  db.collection('game_states').doc(game.id).onSnapshot(
    doc => setupGameboard(doc), 
    err => console.log(err.message)
  );
}

// setup game board
const setupGameboard = (gameStateDoc) => {
  const gameState = gameStateDoc.data();
  gameState.id = gameStateDoc.id;

  var html = '';

  html += `<h3>${gameState.title}</h3><br>`;
  html += `<h5>Players: ${gameState.player_order}</h5><br>`;

  if (!gameState.is_started) {
    html += '<button id="start-game">Start Game</button><br>';
  }

  html += setupGrid(gameState);

  // only if your turn
  html += '<button id="submit">Submit</button>';

  gameBoard.innerHTML = html;

  var elems = document.querySelectorAll('select');
  M.FormSelect.init(elems);

  document.querySelector('#submit').addEventListener('click', e => {
    const selectedSpace = document.querySelector('input[name="grid_space"]:checked');
    if (!selectedSpace) {
      return;
    }
    const x = selectedSpace.dataset['x'];
    const y = selectedSpace.dataset['y'];
    const brand = document.querySelector('#brand-selector').value;
    axios.post(
      'https://us-central1-acquire-538ab.cloudfunctions.net/place_tile',
      { 
        game_id: gameState.id,
        x: x,
        y: y,
        brand: brand
      },
      { headers: { 'Content-Type': 'application/json' }}
    );
  });

  if (!gameState.is_started) {
    document.querySelector('#start-game').addEventListener('click', e => {
      axios.post(
        'https://us-central1-acquire-538ab.cloudfunctions.net/start_game',
        { game_id: gameState.id },
        { headers: { 'Content-Type': 'application/json' }});
    });
  }
}

// map brand to color
const mapBrandToColor = (brand) => {
  map = {
      null: "#c3c3c3",
      'T': "#feac13",
      'L': "#f52d2e",
      'W': "#7a4e28",
      'A': "#092053",
      'F': "#207735",
      'I': "#cf183e",
      'C': "#138199"
  };

  return map[brand];
}

// setup grid
const setupGrid = (gameState) => {
  var html = '<table>';
  const height = gameState.grid[0].length;
  const width = Object.keys(gameState.grid).length;
  
  for (y = 0; y < height; y++) {
    html += '<tr>';
    for (x = 0; x < width; x++) {
      space = gameState.grid[x][y];
      html += '<td>';
        if (space) {
          html += `<svg width="20" height="20">
                      <rect width="20" height="20" style="fill:${mapBrandToColor(space.brand)}"/>
                   </svg>`;
        } else {
          html += `<label><input type="radio" id="grid_space" name="grid_space" data-x="${x}" data-y="${y}"></input><span></span></label>`;
        }
      html += '</td>';
    }
    html += '</tr>';
  }

  html += `
  <div class="input-field col s12 m6">
    <select id="brand-selector" class="icons">
      <option value="" selected></option>
      <option value="F" data-icon="icons/festival.png">Festival</option>
      <option value="W" data-icon="icons/worldwide.png">Worldwide</option>
      <option value="A" data-icon="icons/american.png">American</option>
      <option value="L" data-icon="icons/luxor.png">Luxor</option>
      <option value="I" data-icon="icons/imperial.png">Imperial</option>
      <option value="T" data-icon="icons/tower.png">Tower</option>
      <option value="C" data-icon="icons/continental.png">Continental</option>
    </select>
    <label>Brand</label>
  </div>
  `;

  return html;
};

// setup game list
const setupGameList = (user, docs) => {
  let html = '';
  docs.forEach(doc => {
    const game = doc.data();
    const li = `
      <li>
        <div class="collapsible-header grey lighten-4"> 
          <div>${game.title}</div> 
          <button id="enter-${doc.id}">Join</button>
        </div>
      </li>
    `;
    html += li;
  });
  gameList.innerHTML = html
  docs.forEach(doc => {
    const game = doc.data();
    game.id = doc.id;
    document
      .querySelector(`#enter-${game.id}`)
      .addEventListener('click', e => initGameboard(game));
  });
};

// setup materialize components
document.addEventListener('DOMContentLoaded', function() {

  var modals = document.querySelectorAll('.modal');
  M.Modal.init(modals);

  var items = document.querySelectorAll('.collapsible');
  M.Collapsible.init(items);
});