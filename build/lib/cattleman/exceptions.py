class CattlemanException(RuntimeError):

    def __init__(self, msg: str):
        super(RuntimeError, self).__init__(msg)
