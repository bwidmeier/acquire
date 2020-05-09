// DOM elements
const gameList = document.querySelector('.game-list');
const gameBoard = document.querySelector('.game-board');
const loggedOutLinks = document.querySelectorAll('.logged-out');
const loggedInLinks = document.querySelectorAll('.logged-in');

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
  <div class="row" style="margin-bottom: 0;">
  <div class="col s11">
    <div class="card blue-grey">
      <div style="padding:6px 15px;" class="card-content white-text">
        <span class="card-title">${gameState.title}</span>
        <div style="margin-bottom:0px;" class="row">
          <p style="margin-left:5px;">Tiles left: ${gameState.tiles_remaining}</p>
        </div>
        <div style="margin-bottom:0px;" class="row">`;

  for (const brand of brands) {
    html += `
    <div style="margin:2;" class="col">
    <div class="row" style="margin-bottom:2;">
      <div style="padding:0 0 0 5;" class="col">  
        <svg width="20" height="20">
          <rect width="20" height="20" style="fill:${colorByBrand[brand]}"/>
        </svg>
      </div>
      <div style="padding:0 5;width:25;" class="col">
        <p>${gameState.stock_availability[brand]}</p>
      </div>
    </div>
  </div>`;
  }

  html += '</div></div></div></div><div class="col s1"><a id="showHelpCard" class="btn-floating btn-large waves-effect waves-light green modal-trigger" data-target="modal-help" style="margin:34 0;">?</a></div></div>';

  return html;
};

const setupPlayerInfo = (gameState, playerId) => {
  const cardColor = gameState.current_action_player === playerId ? 'orange' : 'grey';
  
  var html = `
  <div class="col s4 m4">
    <div class="card ${cardColor}">
      <div style="padding:6px 15px;" class="card-content white-text">
        <span class="card-title">${gameState.user_data_by_id[playerId]['display_name']}</span>
        <div style="margin-bottom:4px;" class="row">
          <p style="margin-left:5px;">$${gameState.money_by_player[playerId]}</p>
        </div>
        <div style="margin-bottom:0px;" class="row">
      `;

  for (const brand of brands) {
    html += `
      <div style="margin:0 2;" class="col">
        <div class="row" style="margin-bottom:2;">
          <div style="padding:0 0 0 5;" class="col">  
            <svg width="20" height="20">
              <rect width="20" height="20" style="fill:${colorByBrand[brand]}"/>
            </svg>
          </div>
          <div style="padding:0 5;width:25;" class="col">
            <p>${gameState.stock_by_player[playerId][brand]}</p>
          </div>
        </div>
      </div>`;
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

  var html = '<div id="errorDiv" class="col s12" style="padding:0;"></div>';

  if (!gameState.is_started) {
    html += '<a id="join-game" class="waves-effect waves-light btn">join game</a><br><br>';
    html += '<a id="start-game" class="waves-effect waves-light btn">start game</a><br><br>';
  }

  html += setupGameInfo(gameState);

  html += '<div class="row" style="margin-bottom: 4;">'
    for (const player_id of gameState.player_order) {
      html += setupPlayerInfo(gameState, player_id);
    }
  html += '</div>'

  html += setupGrid(gameState, user, playerTiles);

  html += `
  <div>
    <ul id="actions" class="collection" style="height:200;overflow:auto;">`;
  
  for (const action of gameState.most_recent_actions) {
    html += `<li class="collection-item">${action}</li>`;
  }

  html += `</ul>
  </div>`;

  gameBoard.innerHTML = html;

  var objDiv = document.getElementById("actions");
  objDiv.scrollTop = objDiv.scrollHeight;

  var elems = document.querySelectorAll('select');
  M.FormSelect.init(elems);

  var elems = document.querySelectorAll('.tooltipped');
  M.Tooltip.init(elems, {html: true});

  if (user.uid == gameState.current_action_player && gameState.current_action_type != 'GAME_OVER') {
    document.querySelector('#submit').addEventListener('click', e => {
      if (gameState.current_action_type == 'PLACE') { 
        const selectedSpace = document.querySelector('input[name="grid_space"]:checked');
        if (!selectedSpace) {
          return;
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
              brand: brand
            }
          )
          .then(r => clearError())
          .catch(e => displayError(e.response.data.error));
        });
      } else if (gameState.current_action_type == 'BUY') {
        const festivalInput = document.querySelector('#festivalCount');
        const worldwideInput = document.querySelector('#worldwideCount'); 
        const americanInput = document.querySelector('#americanCount'); 
        const luxorInput = document.querySelector('#luxorCount'); 
        const imperialInput = document.querySelector('#imperialCount'); 
        const towerInput = document.querySelector('#towerCount'); 
        const continentalInput = document.querySelector('#continentalCount'); 
        
        auth.currentUser.getIdToken().then(idToken => {
          axios.post(
            '/buy_stock',
            {
              id_token: idToken,
              game_id: gameState.id,
              purchase_order: {
                F: festivalInput ? festivalInput.value || 0 : 0,
                W: worldwideInput ? worldwideInput.value || 0 : 0,
                A: americanInput ? americanInput.value || 0 : 0,
                L: luxorInput ? luxorInput.value || 0 : 0,
                I: imperialInput ? imperialInput.value || 0 : 0,
                T: towerInput ? towerInput.value || 0 : 0,
                C: continentalInput ? continentalInput.value || 0 : 0
              }
            }
          )
          .then(r => clearError())
          .catch(e => displayError(e.response.data.error));
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
          )
          .then(r => clearError())
          .catch(e => displayError(e.response.data.error));
        });
      }
    });
  }
  
  if (!gameState.is_started) {
    document.querySelector('#start-game').addEventListener('click', e => {
      axios.post(
        '/start_game',
        { game_id: gameState.id }
      )
      .then(r => clearError())
      .catch(e => displayError(e.response.data.error));
    });

    document.querySelector('#join-game').addEventListener('click', e => {
      axios.post(
        '/join_game',
        { 
          game_id: gameState.id, 
          user_id: user.uid 
        }
      )
      .then(r => clearError())
      .catch(e => displayError(e.response.data.error));
    });
  }
}

const displayError = (error) => {
  const errorDiv = document.querySelector('#errorDiv');
    errorDiv.innerHTML = `<div class="row">
    <div class="col s12" style="0 10.5;">
      <div class="card-panel red" style="padding:8; margin:0;">
        <span class="white-text">
          ${error}
        </span>
      </div>
    </div>
  </div>`
};

const clearError = () => {
  const errorDiv = document.querySelector('#errorDiv');
  errorDiv.innerHTML = '';
};

const brands = [
  'T',
  'L',
  'W',
  'A',
  'F',
  'I',
  'C'
];

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
        `;

      for (const brand of gameState.inactive_brands) {
        logo = logoByBrand[brand];
        brandName = brandNameByBrandLetter[brand];
        html += `<option value="${brand}" data-icon="${logo}">${brandName}</option>`;
      }
   
      html += `</select>
      <label>Brand</label>
    </div>`;

      html += '<a id="submit" class="waves-effect waves-light btn">submit</a><br><br>';
    } else if (gameState.current_action_type == 'BUY') {
      html += '<div class="row" style="margin-bottom: 0;">'
      
      for (const brand of gameState.active_brands) {
        const logo = logoByBrand[brand];
        const brandName = brandNameByBrandLetter[brand];
        const inputId = brandName.toLowerCase() + 'Count';
        const cost = gameState.cost_by_brand[brand];
        html += `
          <div class="col" style="right-margin:0; padding: 0 20;">
            <div class="row">
              <div class="col" style="padding:12 0;">
                <img src="${logo}"></img>
              </div>
              <div class="col input-field inline" style="margin:0;">
                <input style="width:120;" type="number" id="${inputId}" min="0" max="3" class="validate">
                <label for="${inputId}">${brandName} @ $${cost}</label>
              </div>
            </div>
          </div>
        `;
      }

      html += '</div><a id="submit" class="waves-effect waves-light btn">submit</a><br><br>';
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
      html += '<td height="50px" width="50px" style="text-align:center;border:thin solid black;padding:5;" ';
      playerHasTile = playerTiles.some(tile => tile['x'] == x && tile['y'] == y);
      if (space) {
        const latestTile = gameState.most_recently_placed_tile;
        const isMostRecent = !latestTile || (x === latestTile.x && y === latestTile.y);
        const size = space.is_locked ? 32 : 20;
        const rectFill = `fill:${colorByBrand[space.brand]};`;
        const rectStyle = isMostRecent ? rectFill + 'stroke:orange;stroke-width:5;' : rectFill;
        const tooltipBrandLine = space.brand ? `<b>Brand: ${brandNameByBrandLetter[space.brand]}</b><br>` : '';
        const tooltip = `${tooltipBrandLine}Chain size: ${space.count}<br>Is safe: ${space.is_locked}`;
        html += `class="tooltipped" data-position="top" data-tooltip="${tooltip}"><svg width="${size}" height="${size}">
                    <rect width="${size}" height="${size}" style="${rectStyle}"/>
                  </svg>`;
      } else if (playerHasTile) {
        html += `><label><input type="radio" id="grid_space" name="grid_space" data-x="${x}" data-y="${y}"></input><span style="padding:0px 25px 0px 0px;"></span></label>`;
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

  var elems = document.querySelectorAll('.tooltipped');
  M.Tooltip.init(elems, {html: true});
});