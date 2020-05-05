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
const initGameboard = (game, user) => {
  gameList.style.display = 'none';
  gameBoard.style.display = 'block';

  db.collection('game_states').doc(game.id).onSnapshot(
    gameStateDoc => {
      const gameState = gameStateDoc.data();
      if (gameState.is_started) {
        db.doc(`game_state_secrets/${gameStateDoc.id}/player_secrets/${user.uid}`).get().then(secretDoc => {
          const tiles = secretDoc.data().tiles;
          setupGameboard(gameStateDoc, user, tiles);
        });
      }
      setupGameboard(gameStateDoc, user, []);
    }, 
    err => console.log(err.message)
  );
};

const setupGameInfo = (gameState) => {
  var html = `
  <div class="col s12 m12">
    <div class="card blue-grey">
      <div style="padding:6px 15px;" class="card-content white-text">
        <span class="card-title">${gameState.title}</span>
        <div style="margin-bottom:0px;" class="row">
          <p style="margin-left:5px;">Tiles left: ${gameState.tiles_remaining}</p>
        </div>
        <div style="margin-bottom:0px;" class="row">`;

  for (const brand in colorByBrand) {
    // EEK!!!
    if (brand === 'null') {
      continue;
    }

    html += `
      <div style="padding:5px;" class="col">
        <svg width="20" height="20">
          <rect width="20" height="20" style="fill:${colorByBrand[brand]}"/>
        </svg>
      </div>
      <div style="padding:5px;" class="col">
        <p>${gameState.stock_availability[brand]}</p>
      </div>`;
  }

  html += '</div></div></div></div>';

  return html;
};

const setupPlayerInfo = (gameState, playerId) => {
  const cardColor = gameState.current_action_player === playerId ? 'orange' : 'grey';
  
  var html = `
  <div class="col s4 m4">
    <div class="card ${cardColor}">
      <div style="padding:6px 15px;" class="card-content white-text">
        <span class="card-title">${gameState.user_data_by_id[playerId]['display_name']}</span>
        <div style="margin-bottom:0px;" class="row">
        <p style="margin-left:5px;">$${gameState.money_by_player[playerId]}</p>
        </div>
        <div style="margin-bottom:0px;" class="row">
      `;

  for (const brand in colorByBrand) {
    // EEK!!!
    if (brand === 'null') {
      continue;
    }

    html += `
      <div style="padding:5px;" class="col">
        <svg width="20" height="20">
          <rect width="20" height="20" style="fill:${colorByBrand[brand]}"/>
        </svg>
      </div>
      <div style="padding:5px;" class="col">
        <p>${gameState.stock_by_player[playerId][brand]}</p>
      </div>`
  }

  html += ` 
  </div> 
  </div>  
      </div>
    </div>`;

  return html;
};

// setup game board
const setupGameboard = (gameStateDoc, user, playerTiles) => {
  const gameState = gameStateDoc.data();
  gameState.id = gameStateDoc.id;

  var html = '';

  if (!gameState.is_started) {
    html += '<a id="join-game" class="waves-effect waves-light btn">join game</a><br><br>';
    html += '<a id="start-game" class="waves-effect waves-light btn">start game</a><br><br>';
  }

  html += setupGameInfo(gameState);

  html += '<div class="row">'
    for (const player_id of gameState.player_order) {
      html += setupPlayerInfo(gameState, player_id);
    }
  html += '</div>'

  html += setupGrid(gameState, user, playerTiles);

  gameBoard.innerHTML = html;

  var elems = document.querySelectorAll('select');
  M.FormSelect.init(elems);

  if (user.uid == gameState.current_action_player && gameState.current_action_type != 'GAME_OVER') {
    document.querySelector('#submit').addEventListener('click', e => {
      if (gameState.current_action_type == 'PLACE') { 
        const selectedSpace = document.querySelector('input[name="grid_space"]:checked');
        if (!selectedSpace) {
          // stopgap until backend gives players new tiles if they can't play (or skips their placement phase if they still can't)
          // return;
          auth.currentUser.getIdToken().then(idToken => {
            axios.post(
              '/place_tile',
              { 
                id_token: idToken,
                game_id: gameState.id,
                skip: true
              }
            );
          });
        }
        const x = selectedSpace.dataset['x'];
        const y = selectedSpace.dataset['y'];
        const brand = document.querySelector('#brand-selector').value;
        auth.currentUser.getIdToken().then(idToken => {
          axios.post(
            '/place_tile',
            { 
              id_token: idToken,
              game_id: gameState.id,
              x: x,
              y: y,
              brand: brand,
              skip: false
            }
          );
        });
      } else if (gameState.current_action_type == 'BUY') {
        const festivalCount = document.querySelector('#festivalCount').value;
        const worldwideCount = document.querySelector('#worldwideCount').value; 
        const americanCount = document.querySelector('#americanCount').value; 
        const luxorCount = document.querySelector('#luxorCount').value; 
        const imperialCount = document.querySelector('#imperialCount').value; 
        const towerCount = document.querySelector('#towerCount').value; 
        const continentalCount = document.querySelector('#continentalCount').value; 
        
        auth.currentUser.getIdToken().then(idToken => {
          axios.post(
            '/buy_stock',
            {
              id_token: idToken,
              game_id: gameState.id,
              purchase_order: {
                F: festivalCount || 0,
                W: worldwideCount || 0,
                A: americanCount || 0,
                L: luxorCount || 0,
                I: imperialCount || 0,
                T: towerCount || 0,
                C: continentalCount || 0
              }
            }
          );
        });
      } else if (gameState.current_action_type == 'RESOLVE') {
        const sellCount = document.querySelector('#sellCount').value;
        const tradeCount = document.querySelector('#tradeCount').value;

        auth.currentUser.getIdToken().then(idToken => {
          axios.post(
            '/resolve_acquisition',
            {
              id_token: idToken,
              game_id: gameState.id,
              sell_count: sellCount || 0,
              trade_count: tradeCount || 0
            }
          );
        });
      }
    });
  }
  
  if (!gameState.is_started) {
    document.querySelector('#start-game').addEventListener('click', e => {
      axios.post(
        '/start_game',
        { game_id: gameState.id });
    });

    document.querySelector('#join-game').addEventListener('click', e => {
      axios.post(
        '/join_game',
        { 
          game_id: gameState.id, 
          user_id: user.uid 
        });
    });
  }
}

// map brand to color
const colorByBrand = {
  null: "#c3c3c3",
  'F': "#207735",
  'W': "#7a4e28",
  'A': "#092053",
  'L': "#f52d2e",
  'I': "#cf183e",
  'T': "#feac13",
  'C': "#138199"
}

const brandNameByBrandLetter = {
  'F': "Festival",
  'W': "Worldwide",
  'A': "American",
  'L': "Luxor",
  'I': "Imperial",
  'T': "Tower",
  'C': "Continental"
}

const logoByBrand = {
  'F': "img/festival.png",
  'W': "img/worldwide.png",
  'A': "img/american.png",
  'L': "img/luxor.png",
  'I': "img/imperial.png",
  'T': "img/tower.png",
  'C': "img/continental.png"
}

// setup grid
const setupGrid = (gameState, user, playerTiles) => {
  var html = '';

  if (user.uid == gameState.current_action_player) {
    if (gameState.current_action_type == 'PLACE') {
      html += `
      <div class="input-field col s12 m6">
        <select id="brand-selector" class="icons">
          <option value="" selected></option>
          <option value="F" data-icon="img/festival.png">Festival</option>
          <option value="W" data-icon="img/worldwide.png">Worldwide</option>
          <option value="A" data-icon="img/american.png">American</option>
          <option value="L" data-icon="img/luxor.png">Luxor</option>
          <option value="I" data-icon="img/imperial.png">Imperial</option>
          <option value="T" data-icon="img/tower.png">Tower</option>
          <option value="C" data-icon="img/continental.png">Continental</option>
        </select>
        <label>Brand</label>
      </div>
      `;

      html += '<a id="submit" class="waves-effect waves-light btn">submit</a><br><br>';
    } else if (gameState.current_action_type == 'BUY') {
      html += `
      <table><tr>
        <!-- Festival -->
        <td><img src='img/festival.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="festivalCount" min="0" max="3" class="validate">
            <label for="festivalCount">Festival</label>
        </div></td>

        <!-- Worldwide -->
        <td><img src='img/worldwide.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="worldwideCount" min="0" max="3" class="validate">
            <label for="worldwideCount">Worldwide</label>
        </div></td>

        <!-- American -->
        <td><img src='img/american.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="americanCount" min="0" max="3" class="validate">
            <label for="americanCount">American</label>
        </div></td>

        <!-- Luxor -->
        <td><img src='img/luxor.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="luxorCount" min="0" max="3" class="validate">
            <label for="luxorCount">Luxor</label>
        </div></td>

        <!-- Imperial -->
        <td><img src='img/imperial.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="imperialCount" min="0" max="3" class="validate">
            <label for="imperialCount">Imperial</label>
        </div></td>

        <!-- Tower -->
        <td><img src='img/tower.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="towerCount" min="0" max="3" class="validate">
            <label for="towerCount">Tower</label>
        </div></td>

        <!-- Continental -->
        <td><img src='img/continental.png'></img></td>
        <td><div class="input-field inline">
            <input type="number" id="continentalCount" min="0" max="3" class="validate">
            <label for="continentalCount">Continental</label>
        </div></td>
      </tr></table>
      `;

      html += '<a id="submit" class="waves-effect waves-light btn">submit</a><br><br>';
    } else if (gameState.current_action_type == 'RESOLVE') {
      const acquiree = gameState.current_action_details.acquiree
      const cost = gameState.current_action_details.acquiree_cost_at_acquisition_time
      const logo = logoByBrand[acquiree]
      const acquirer = brandNameByBrandLetter[gameState.current_action_details.acquirer]

      html += `
      <div class="row">
        <div class="col">
          <img src="${logo}" style="padding:22.5px;"></img>
        </div>
        <div class="col">
          <div class="input-field inline">
            <input type="number" id="sellCount" min="0" class="validate">
            <label for="sellCount">Sell @ $${cost}</label>
          </div>
        </div>
        <div class="col">
          <div class="input-field inline">
            <input type="number" id="tradeCount" min="0" step="2" class="validate">
            <label for="tradeCount">Trade for ${acquirer}</label>
          </div>
        </div>
      </div>
      `

      html += '<a id="submit" class="waves-effect waves-light btn">submit</a><br><br>';
    } 
  }
  
  if (gameState.current_action_type == 'GAME_OVER') {
    html += '<h1>GG!!!!!!!!!</h1>';
  }

  html  += '<table>';
  const height = gameState.grid[0].length;
  const width = Object.keys(gameState.grid).length;  

  for (y = 0; y < height; y++) {
    html += '<tr>';
    for (x = 0; x < width; x++) {
      space = gameState.grid[x][y];
      html += '<td height="50px" width="50px" style="text-align:center;border:thin solid black;">';
      playerHasTile = playerTiles.some(tile => tile['x'] == x && tile['y'] == y);
      if (space) {
        html += `<svg width="20" height="20">
                    <rect width="20" height="20" style="fill:${colorByBrand[space.brand]}"/>
                  </svg>`;
      } else if (playerHasTile) {
        html += `<label><input type="radio" id="grid_space" name="grid_space" data-x="${x}" data-y="${y}"></input><span style="padding:0px 25px 0px 0px;"></span></label>`;
      }
      html += '</td>';
    }
    html += '</tr>';
  }

  html += '</table>'

  return html;
};

// setup game list
const setupGameList = (user, docs) => {
  let html = '';
  docs.forEach(doc => {
    const game = doc.data();
    const li = `
    <div class="card grey darken">
      <div style="padding:6px 15px;" class="card-content white-text">
        <div class="row" style="margin:0px;">
          <div class="col">
            <span class="card-title">${game.title}</span>
          </div>
          <div class="col right">
            <a id="enter-${doc.id}" class="waves-effect waves-light btn">enter</a>
          </div>
        </div>
      </div>
    </div>
    `;
    html += li;
  });
  gameList.innerHTML = html
  docs.forEach(doc => {
    const game = doc.data();
    game.id = doc.id;
    document
      .querySelector(`#enter-${game.id}`)
      .addEventListener('click', e => initGameboard(game, user));
  });
};

// setup materialize components
document.addEventListener('DOMContentLoaded', function() {

  var modals = document.querySelectorAll('.modal');
  M.Modal.init(modals);

  var items = document.querySelectorAll('.collapsible');
  M.Collapsible.init(items);
});