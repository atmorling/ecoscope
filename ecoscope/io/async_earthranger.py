import json
import geopandas as gpd
import pandas as pd
import asyncio
from erclient.client import AsyncERClient
from ecoscope.io.utils import to_hex

import ecoscope


def fatal_status_code(e):
    return 400 <= e.response.status_code < 500


class AsyncEarthRangerIO(AsyncERClient):
    def __init__(self, sub_page_size=4000, tcp_limit=5, **kwargs):
        if "server" in kwargs:
            server = kwargs.pop("server")
            kwargs["service_root"] = f"{server}/api/v1.0"
            kwargs["token_url"] = f"{server}/oauth2/token"

        self.sub_page_size = sub_page_size
        self.tcp_limit = tcp_limit
        kwargs["client_id"] = kwargs.get("client_id", "das_web_client")
        super().__init__(**kwargs)

    @staticmethod
    def _clean_kwargs(addl_kwargs={}, **kwargs):
        for k in addl_kwargs.keys():
            print(f"Warning: {k} is a non-standard parameter. Results may be unexpected.")
        return {k: v for k, v in {**addl_kwargs, **kwargs}.items() if v is not None}

    @staticmethod
    def _normalize_column(df, col):
        print(col)
        for k, v in pd.json_normalize(df.pop(col), sep="__").add_prefix(f"{col}__").items():
            df[k] = v.values

    @staticmethod
    def _dataframe_to_dict(events):
        if isinstance(events, gpd.GeoDataFrame):
            events["location"] = pd.DataFrame({"longitude": events.geometry.x, "latitude": events.geometry.y}).to_dict(
                "records"
            )
            del events["geometry"]

        if isinstance(events, pd.DataFrame):
            events = events.to_dict("records")
        return events

    @staticmethod
    def _to_gdf(df):
        longitude, latitude = (0, 1) if isinstance(df["location"].iat[0], list) else ("longitude", "latitude")
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["location"].str[longitude], df["location"].str[latitude]),
            crs=4326,
        )

    async def _get_sources_generator(
        self,
        manufacturer_id=None,
        provider_key=None,
        provider=None,
        id=None,
        **addl_kwargs,
    ):
        """
        Parameters
        ----------
        manufacturer_id
        provider_key
        providers
        id
        Returns
        -------
        sources : pd.DataFrame
            DataFrame of queried sources
        """

        params = self._clean_kwargs(
            addl_kwargs,
            manufacturer_id=manufacturer_id,
            provider_key=provider_key,
            provider=provider,
            id=id,
            page_size=4000,
        )

        async for source in self._get_data("sources/", params=params):
            yield source

    async def _get_sources_dataframe(self, **kwargs):
        sources = []
        async for source in self._get_sources_generator(**kwargs):
            sources.append(source)

        return pd.DataFrame(sources)

    def get_sources(self, **kwargs):
        return asyncio.get_event_loop().run_until_complete(self._get_sources_dataframe(**kwargs))

    async def _get_subjects_generator(
        self,
        include_inactive=None,
        bbox=None,
        subject_group_id=None,
        name=None,
        updated_since=None,
        tracks=None,
        id=None,
        updated_until=None,
        subject_group_name=None,
        **addl_kwargs,
    ):
        """
        Parameters
        ----------
        include_inactive: Include inactive subjects in list.
        bbox: Include subjects having track data within this bounding box defined by a 4-tuple of coordinates marking
            west, south, east, north.
        subject_group_id: Indicate a subject group id for which Subjects should be listed.
            This is translated to the subject_group parameter in the ER backend
        name : Find subjects with the given name
        updated_since: Return Subject that have been updated since the given timestamp.
        tracks: Indicate whether to render each subject's recent tracks.
        id: A comma-delimited list of Subject IDs.
        updated_until
        subject_group_name: A subject group name for which Subjects should be listed.
            This is translated to the group_name parameter in the ER backend
        Returns
        -------
        subjects : pd.DataFrame
        """

        params = self._clean_kwargs(
            addl_kwargs,
            include_inactive=include_inactive,
            bbox=bbox,
            subject_group=subject_group_id,
            name=name,
            updated_since=updated_since,
            tracks=tracks,
            id=id,
            updated_until=updated_until,
            group_name=subject_group_name,
            page_size=4000,
        )

        assert params.get("subject_group") is None or params.get("group_name") is None

        if params.get("group_name") is not None:
            try:
                params["subject_group"] = await self._get_data(
                    "subjectgroups/",
                    params={
                        "group_name": params.pop("group_name"),
                        "include_inactive": True,
                        "include_hidden": True,
                        "flat": True,
                    },
                )[0]["id"]
            except IndexError:
                raise KeyError("`group_name` not found")

        async for source in self._get_data("subjects/", params=params):
            yield source

    async def _get_subjects_dataframe(self, **kwargs):
        subjects = []
        async for subject in self._get_subjects_generator(**kwargs):
            subjects.append(subject)

        df = pd.DataFrame(subjects)
        assert not df.empty
        df["hex"] = df["additional"].str["rgb"].map(to_hex) if "additional" in df else "#ff0000"

        return df

    def get_subjects(self, **kwargs):
        return asyncio.get_event_loop().run_until_complete(self._get_subjects_dataframe(**kwargs))

    async def _get_subjectsources_generator(self, subjects=None, sources=None, **addl_kwargs):
        """
        Parameters
        ----------
        subjects: A comma-delimited list of Subject IDs.
        sources: A comma-delimited list of Source IDs.
        Returns
        -------
        subjectsources : pd.DataFrame
        """
        params = self._clean_kwargs(addl_kwargs, sources=sources, subjects=subjects)

        async for subjectsource in self._get_data("subjectsources/", params=params):
            yield subjectsource

    async def _get_subjectsources_dataframe(self, **kwargs):
        subject_sources = []
        async for subject_source in self._get_subjectsources_generator(**kwargs):
            subject_sources.append(subject_source)

        df = pd.DataFrame(subject_sources)
        return df

    async def get_patrols(self, since=None, until=None, patrol_type=None, status=None, **addl_kwargs):
        """
        Parameters
        ----------
        since:
            lower date range
        until:
            upper date range
        patrol_type:
            Comma-separated list of type of patrol UUID
        status
            Comma-separated list of 'scheduled'/'active'/'overdue'/'done'/'cancelled'
        Returns
        -------
        patrols : pd.DataFrame
            DataFrame of queried patrols
        """

        params = self._clean_kwargs(
            addl_kwargs,
            status=status,
            patrol_type=[patrol_type] if isinstance(patrol_type, str) else patrol_type,
            return_data=True,
        )

        filter = {"date_range": {}, "patrol_type": []}

        if since is not None:
            filter["date_range"]["lower"] = since
        if until is not None:
            filter["date_range"]["upper"] = until
        if patrol_type is not None:
            filter["patrol_type"] = params["patrol_type"]
        params["filter"] = json.dumps(filter)

        async for patrol in self._get_data("activity/patrols", params=params):
            yield patrol

    async def get_patrol_observations(
        self,
        since=None,
        until=None,
        patrol_type=None,
        status=None,
        include_patrol_details=False,
        relocations=True,
        tz="UTC",
        **kwargs,
    ):
        """
        Download observations for provided `patrols_df`.

        Parameters
        ----------
        patrols_df : pd.DataFrame
           Data returned from a call to `get_patrols`.
        include_patrol_details : bool, optional
           Whether to merge patrol details into dataframe
        kwargs
           Additional parameters to pass to `get_subject_observations`.

        Returns
        -------
        relocations : ecoscope.base.Relocations
        """

        """patrols struct
        {'id': 'ea2b9c29-a9f1-4a32-9634-962690d96618',
         'priority': 0,
         'state': 'done',
         'objective': None,
         'serial_number': 14150,
         'title': 'End of foot patrol starting motorbike back to camp',
         'files': [],
         'notes': [],
         'patrol_segments': [{'id': '751a5d54-42dc-4c8b-9416-68d77577d32a', 'patrol_type': 'mwaluganje_routine_motorbike_patrol', 'leader': {'content_type': 'observations.subject', 'id': 'e146c97b-912b-430c-95b2-4e9c3a2186c6', 'name': 'Suleiman Kibo', 'subject_type': 'person', 'subject_subtype': 'ranger', 'common_name': None, 'additional': {'rgb': '200, 70, 146', 'sex': '', 'region': 'Rangers-MEP', 'country': 'Kenya', 'external_id': '', 'tm_animal_id': '', 'external_name': ''}, 'created_at': '2024-01-23T10:38:53.337249+03:00', 'updated_at': '2024-06-30T10:50:30.734207+03:00', 'is_active': True, 'user': {'id': '0b6a95fa-3295-4e78-9b3a-9aee19ae5a48'}, 'region': 'Rangers-MEP', 'country': 'Kenya', 'sex': '', 'tracks_available': False, 'image_url': '/static/ranger-black.svg'}, 'scheduled_start': None, 'scheduled_end': None, 'time_range': {'start_time': '2024-05-24T11:01:06+03:00', 'end_time': '2024-05-24T11:33:00+03:00'}, 'start_location': {'latitude': -4.0904833, 'longitude': 39.465905}, 'end_location': {'latitude': -4.074973, 'longitude': 39.4845189}, 'events': [], 'image_url': 'https://mep.pamdas.org/static/sprite-src/traffic_rep.svg', 'icon_id': 'traffic_rep', 'updates': [{'message': 'Updated fields: End Time', 'time': '2024-05-25T12:51:12.164228+00:00', 'user': {'username': 'ckagume', 'first_name': 'Caroline', 'last_name': 'Mumbi', 'id': '06c5ea42-5041-4cf1-9360-d556dddca3e2', 'content_type': 'accounts.user'}, 'type': 'update_segment'}, {'message': 'Updated fields: End Time, End Location', 'time': '2024-05-24T08:39:09.737928+00:00', 'user': {'username': 'karani', 'first_name': 'Suleiman', 'last_name': 'Kibo', 'id': '0b6a95fa-3295-4e78-9b3a-9aee19ae5a48', 'content_type': 'accounts.user'}, 'type': 'update_segment'}]}], 'updates': [{'message': 'Updated fields: State is done', 'time': '2024-05-24T08:39:09.757917+00:00', 'user': {'username': 'karani', 'first_name': 'Suleiman', 'last_name': 'Kibo', 'id': '0b6a95fa-3295-4e78-9b3a-9aee19ae5a48', 'content_type': 'accounts.user'}, 'type': 'update_patrol_state'}, {'message': 'Patrol Added', 'time': '2024-05-24T08:01:28.516621+00:00', 'user': {'username': 'karani', 'first_name': 'Suleiman', 'last_name': 'Kibo', 'id': '0b6a95fa-3295-4e78-9b3a-9aee19ae5a48', 'content_type': 'accounts.user'}, 'type': 'add_patrol'}]}
        """  # noqa

        observations = ecoscope.base.Relocations()
        # ignoring patrol types for now
        # patrol_types = await self._get_data("activity/patrols/types", params={})

        tasks = []
        async for patrol in self.get_patrols(since=since, until=until, patrol_type=patrol_type, status=status):
            task = asyncio.create_task(self._get_observations(patrol, relocations, tz, **kwargs))
            tasks.append(task)

        observations = await asyncio.gather(*tasks)
        observations = pd.concat(observations)
        # if include_patrol_details:
        #     return df.set_index("id")
        return observations

    async def _get_observations(self, patrol, relocations=True, tz="UTC", **kwargs):

        observations = ecoscope.base.Relocations()
        for patrol_segment in patrol["patrol_segments"]:
            subject_id = (patrol_segment.get("leader") or {}).get("id")
            patrol_start_time = (patrol_segment.get("time_range") or {}).get("start_time")
            patrol_end_time = (patrol_segment.get("time_range") or {}).get("end_time")

            # ignoring patrol types for now
            # patrol_type = df_pt[df_pt["value"] == patrol_segment.get("patrol_type")].reset_index()["id"][0]

            if None in {subject_id, patrol_start_time}:
                continue

            try:
                observations_by_subject = []
                async for obs in self.get_observations(
                    subject_id=subject_id, start=patrol_start_time, end=patrol_end_time, **kwargs
                ):
                    observations_by_subject.append(obs)

                observations_by_subject = pd.DataFrame(observations_by_subject)
                if observations_by_subject.empty:
                    continue

                observations_by_subject["subject_id"] = subject_id
                observations_by_subject["created_at"] = pd.to_datetime(
                    observations_by_subject["created_at"],
                    errors="coerce",
                    utc=True,
                ).dt.tz_convert(tz)

                observations_by_subject["recorded_at"] = pd.to_datetime(
                    observations_by_subject["recorded_at"],
                    errors="coerce",
                    utc=True,
                ).dt.tz_convert(tz)
                observations_by_subject.sort_values("recorded_at", inplace=True)
                observations_by_subject = self._to_gdf(observations_by_subject)

                # TODO - handle include flag requests
                #  include_source_details
                #  include_subject_details
                #  include_subjectsource_details

                if relocations:
                    observations_by_subject = ecoscope.base.Relocations.from_gdf(
                        observations_by_subject,
                        groupby_col="subject_id",
                        uuid_col="id",
                        time_col="recorded_at",
                    )

                # TODO re-add handling for patrol details

                if len(observations_by_subject) > 0:
                    observations = pd.concat([observations, observations_by_subject])

            except Exception as e:
                print(
                    f"Getting observations for subject_id={subject_id} start_time={patrol_start_time}"
                    f"end_time={patrol_end_time} failed for: {e}"
                )
        return observations
