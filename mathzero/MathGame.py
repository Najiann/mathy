import numpy
from .MathBoard import MathBoard
import random
import spacy

class MathGame:
    """
    Implement a math solving game where players have two distinct win conditions
    that require different strategies for solving. The first win-condition is for 
    the player to execute the right sequence of actions to reduce a math expression
    to its most basic representation. The second is for the other player to expand 
    the simple representations into more verbose expressions.

    Ideally a fully-trained player will be able to both simplify arbitrary mathematical
    expressions, and expand upon arbitrary parts of expressions to generate more complex
    representations that can be used to expand on concepts that a user may struggle with.
    """

    def __init__(self, width=64, history_length=64):
        self.width = width
        self.history_length = history_length

    def getInitBoard(self):
        """
        Returns:
            startBoard: a representation of the board (ideally this is the form
                        that will be the input to your neural network)
        """
        b = MathBoard(self.width, self.history_length)
        return numpy.array(b.pieces)

    def getBoardSize(self):
        """
        Returns:
            (x,y): a tuple of board dimensions
        """
        return (self.width, self.history_length)

    def getActionSize(self):
        """
        Returns:
            actionSize: number of all possible actions
        """
        return 0

    def getNextState(self, board, player, action):
        """
        Input:
            board: current board
            player: current player (1 or -1)
            action: action taken by current player

        Returns:
            nextBoard: board after applying action
            nextPlayer: player who plays in the next turn (should be -player)
        """
        print("action taken!: {}".format(action))
        board[0][0] = random.randint(0,100)
        return board, player

    def getValidMoves(self, board, player):
        """
        Input:
            board: current board
            player: current player

        Returns:
            validMoves: a binary vector of length self.getActionSize(), 1 for
                        moves that are valid from the current board and player,
                        0 for invalid moves
        """
        return [0] * self.getActionSize()

    def getGameEnded(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            r: 0 if game has not ended. 1 if player won, -1 if player lost,
               small non-zero value for draw.
               
        """
        return 0

    def getCanonicalForm(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            canonicalBoard: returns canonical form of board. The canonical form
                            should be independent of player. For e.g. in chess,
                            the canonical form can be chosen to be from the pov
                            of white. When the player is white, we can return
                            board as is. When the player is black, we can invert
                            the colors and return the board.
        """
        return board

    def getSymmetries(self, board, pi):
        """
        Input:
            board: current board
            pi: policy vector of size self.getActionSize()

        Returns:
            symmForms: a list of [(board,pi)] where each tuple is a symmetrical
                       form of the board and the corresponding pi vector. This
                       is used when training the neural network from examples.
        """
        return []

    def stringRepresentation(self, board):
        """
        Input:
            board: current board

        Returns:
            boardString: a quick conversion of board to a string format.
                         Required by MCTS for hashing.
        """
        return str(board)
