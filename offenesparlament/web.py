#coding: utf-8
from collections import defaultdict
from datetime import datetime
from urllib import quote
import re

from flask import Flask, g, request, render_template, abort, flash, json
from flask import url_for, redirect, jsonify, Response, make_response

from offenesparlament.core import app, pages, db
from offenesparlament.model import Ablauf, Position, Abstimmung, Stimme
from offenesparlament.model import Person, Dokument
from offenesparlament.model import Sitzung, Zitat, Debatte
from offenesparlament.model import Abo

from offenesparlament.lib.pager import Pager
from offenesparlament.lib.seo import render_sitemap
from offenesparlament.util import jsonify, make_feed
from offenesparlament.lib.searcher import SolrSearcher
from offenesparlament.data import aggregates
from offenesparlament.views.filters import drslink
from offenesparlament.views.abo import abo
from offenesparlament.views.person import person
from offenesparlament.views.ablauf import ablauf
from offenesparlament.views.abstimmung import abstimmung

app.register_blueprint(abo)
app.register_blueprint(person)
app.register_blueprint(ablauf)
app.register_blueprint(abstimmung)

@app.route("/plenum/<wahlperiode>/<nummer>/<debatte>")
@app.route("/plenum/<wahlperiode>/<nummer>/<debatte>.<format>")
def debatte(wahlperiode, nummer, debatte, format=None):
    debatte = Debatte.query.filter_by(nummer=debatte)\
            .join(Sitzung)\
            .filter(Sitzung.wahlperiode == wahlperiode)\
            .filter(Sitzung.nummer == nummer).first()
    if debatte is None:
        abort(404)
    if format == 'json':
        return jsonify(debatte)
    sitzung_url = url_for('sitzung', wahlperiode=wahlperiode, nummer=nummer)
    url = sitzung_url + '?debatte.titel=' + quote(debatte.titel.encode('utf-8'))
    url = url + '&paging=false'
    return redirect(url)


@app.route("/plenum/<wahlperiode>/<nummer>")
@app.route("/plenum/<wahlperiode>/<nummer>.<format>")
def sitzung(wahlperiode, nummer, format=None):
    sitzung = Sitzung.query.filter_by(wahlperiode=wahlperiode,
                                      nummer=nummer).first()
    if sitzung is None:
        abort(404)
    searcher = SolrSearcher(Zitat, request.args)
    searcher.filter('sitzung.wahlperiode', sitzung.wahlperiode)
    searcher.filter('sitzung.nummer', sitzung.nummer)
    searcher.add_facet('debatte.titel')
    searcher.add_facet('redner')
    searcher.sort('sequenz', 'asc')
    pager = Pager(searcher, 'sitzung', request.args,
            wahlperiode=wahlperiode, nummer=nummer)
    pager.limit = 100
    if format == 'json':
        data = sitzung.to_dict()
        data['results'] = pager
        return jsonify(data)
    return render_template('sitzung_view.html',
            sitzung=sitzung, pager=pager, searcher=searcher)

@app.route("/sitemap/plenum-<year>.xml")
def plenum_sitemap(year):
    items = []
    query = Debatte.query.join(Sitzung)
    query = query.filter(db.extract('year', Sitzung.date)==int(year))
    query = query.distinct(Debatte.id)
    for debatte in query:
        item = {'lastmod': debatte.updated_at,
                'loc': url_for('debatte', wahlperiode=debatte.sitzung.wahlperiode,
                               nummer=debatte.sitzung.nummer, debatte=debatte.id,
                               _external=True)}
        items.append(item)
    return render_sitemap(items, prio=0.9)


@app.route("/plenum")
@app.route("/plenum.<format>")
def sitzungen(format=None):
    searcher = SolrSearcher(Sitzung, request.args)
    searcher.add_facet('wahlperiode')
    searcher.sort('date', 'desc')
    pager = Pager(searcher, 'sitzungen', request.args)
    if format == 'json':
        return jsonify({'results': pager})
    return render_template('sitzung_search.html',
            searcher=searcher, pager=pager)



@app.route("/pages/<path:path>")
def page(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)


@app.route("/sitemap.xml")
def sitemap():
    now = datetime.utcnow()
    years = range(2000, now.year+1)[::-1]
    res = make_response(render_template('sitemapindex.xml',
        years=years, now=now, url=url_for('index', _external=True)))
    res.headers['Content-Type'] = 'text/xml; charset=utf-8'
    return res

@app.route("/robots.txt")
def robots_txt():
    res = make_response(render_template('robots.txt'))
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

@app.route("/")
def index():
    general = aggregates.current_schlagworte()
    sachgebiete = aggregates.sachgebiete()
    sitzung = Sitzung.query.order_by(Sitzung.nummer.desc()).first()
    return render_template('home.html', general=general,
            sachgebiete=sachgebiete, sitzung=sitzung)

if __name__ == '__main__':
    app.debug = True
    app.run(port=5006)
