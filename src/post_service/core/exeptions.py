from fastapi import HTTPException, status


class PostServiceException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class PostNotFoundError(PostServiceException):
    def __init__(self, post_id: str):
        super().__init__(detail=f"Post with id {post_id} not found",
                         status_code=status.HTTP_404_NOT_FOUND)


class PostAccessDeniedError(PostServiceException):
    def __init__(self):
        super().__init__(detail="Access to post denied",
                         status_code=status.HTTP_403_FORBIDDEN)


class InvalidPostDataError(PostServiceException):
    def __init__(self, detail: str = "Invalid post data"):
        super().__init__(detail=detail,
                         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseError(PostServiceException):
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(detail=detail,
                         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)