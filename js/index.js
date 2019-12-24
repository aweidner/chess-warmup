const databaseLocation = "database.json";
var database = null;

var board = null;
var game = new Chess();
var tactic = null;
var currentLine = null;

async function getDatabase() {
    const response = await fetch(databaseLocation);
    database = await response.json();
    return database
}

function pickRandomTactic() {
    const tacticId = Math.floor(Math.random() * database.length + 1);
    tactic = database[tacticId];
    currentLine = tactic['l'];
    board.position(tactic['f']);
    game.load(tactic['f']);
    board.orientation(tactic['c']);
}

async function initialize() {
    await getDatabase();
    pickRandomTactic()
}

function onDragStart (source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // only pick up pieces for the side to move
  if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
      (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
    return false
  }
}

function evaluateMove(source, target) {
    const move = source + target
    if (move in currentLine) {
        nextLine = currentLine[move]

        if (nextLine == "retry") {
            return false;
        }

        if (nextLine == "win") {
            $("#success").show();
            setTimeout(function() {
                pickRandomTactic();
                $("#success").hide();
            }, 2000);
        }

        currentLine = nextLine

        game.move({
            from: source,
            to: target,
            promotion: 'q'
        })

        return true;
    }
    return false;
}
function onDrop (source, target) {
    if (!evaluateMove(source, target)) {
        return 'snapback'
    }

    if (currentLine == "win") {
        return;
    }

    const nextMove = Object.keys(currentLine)[0]
        
    opSource = nextMove.substring(0, 2)
    opDest = nextMove.substring(2)

    setTimeout(function() {
        board.move(opSource + "-" + opDest);
        evaluateMove(opSource, opDest);
    }, 300);
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
    board.position(game.fen())
}

board = Chessboard('board', {
    "draggable": true,
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd
});

initialize();
