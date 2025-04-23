from typing import TypeVar

from classes_out import ListenHistoryOut, TracksOut, UsersOut
from fastapi import FastAPI, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from generate_fake_data import FakeDataGenerator

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseParamsFields(size=Query(100, ge=1, le=100)),
]

app = FastAPI(
    title="MooVitamix",
    description="A music recommendation system.",
    version="1.1",
    docs_url=None,
)


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/docs", include_in_schema=False)
async def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="MooVitamix",
        swagger_favicon_url="https://moov.ai/wp-content/uploads/2019/07/cropped-favicon-1-32x32.png",
    )


data_range_observations = 1000
generator = FakeDataGenerator(data_range_observations)
tracks, users, listen_history = generator.generate_fake_data()


@app.get("/tracks", response_model=CustomPage[TracksOut], tags=["HTTP methods"])
async def get_tracks() -> CustomPage[TracksOut]:
    return paginate(tracks)


@app.get("/users", response_model=CustomPage[UsersOut], tags=["HTTP methods"])
async def get_users() -> CustomPage[UsersOut]:
    return paginate(users)


@app.get("/listen_history", response_model=CustomPage[ListenHistoryOut], tags=["HTTP methods"])
async def get_listen_history() -> CustomPage[ListenHistoryOut]:
    return paginate(listen_history)


add_pagination(app)
