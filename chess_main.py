import chess_view
import chess_controller


def main():
    """Main
       Initiates the controller of the
       application and displays the main menu
       (while waiting for user events)
    """
    controller = chess_controller.ChessController(chess_view.View())
    controller.play_game()


if __name__ == "__main__":
    main()
