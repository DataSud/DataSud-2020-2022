# encoding: utf-8

from sqlalchemy import types, Column, Table, text

import meta
import domain_object

__all__ = ['tracking_summary_table', 'TrackingSummary', 'tracking_raw_table']

tracking_raw_table = Table('tracking_raw', meta.metadata,
        Column('user_key', types.Unicode(100), nullable=False),
        Column('url', types.UnicodeText, nullable=False),
        Column('tracking_type', types.Unicode(10), nullable=False),
        Column('access_timestamp', types.DateTime),
    )


tracking_summary_table = Table('tracking_summary', meta.metadata,
        Column('url', types.UnicodeText, primary_key=True, nullable=False),
        Column('package_id', types.UnicodeText),
        Column('tracking_type', types.Unicode(10), nullable=False),
        Column('count', types.Integer, nullable=False),
        Column('running_total', types.Integer, nullable=False),
        Column('recent_views', types.Integer, nullable=False),
        Column('tracking_date', types.DateTime),
    )

class TrackingSummary(domain_object.DomainObject):

    @classmethod
    def get_for_package(cls, package_id):
        obj = meta.Session.query(cls).autoflush(False)
        obj = obj.filter_by(package_id=package_id)
        data = obj.order_by('tracking_date desc').first()
        if data:
            return {'total' : data.running_total,
                    'recent': data.recent_views,
                    'download': cls.get_total_download(package_id)}

        return {'total' : 0, 'recent' : 0, 'download' : 0}

    @classmethod
    def get_for_resource(cls, url):
        obj = meta.Session.query(cls).autoflush(False)
        data = obj.filter_by(url=url).order_by('tracking_date desc').first()
        if data:
            return {'total' : data.running_total,
                    'recent': data.recent_views}

        return {'total' : 0, 'recent' : 0}

    @classmethod
    def get_total_download(cls, package_id):
        url = '%dataset/{package_id}/resource/%/download%'.format(package_id=package_id)
        query = text("""
            SELECT SUM(running_total)::int AS total_download FROM (
              SELECT DISTINCT ON (url) running_total, tracking_date
              FROM tracking_summary WHERE url LIKE :url ORDER BY url, tracking_date DESC) AS sub;
            """)

        result = meta.Session.execute(query, {'url': url}).fetchone()
        return result.total_download or 0

meta.mapper(TrackingSummary, tracking_summary_table)
