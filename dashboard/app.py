# import dependiencies
import os

import pandas as pd
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from flask import Flask, render_template, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy

# initialize the flask app
app = Flask(__name__)

# database setup
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', '') or "sqlite:///db/bellybutton.sqlite"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(db.engine, reflect=True)

# save references to each table
Samples_Metadata = Base.classes.sample_metadata
Samples = Base.classes.samples

# home route
@app.route("/")
def index():
    """Return the homepage."""
    return render_template("index.html")

# name route
@app.route("/names")
def names():
    """Return a list of sample names."""

    # use Pandas to perform the sql query
    stmt = db.session.query(Samples).statement
    df = pd.read_sql_query(stmt, db.session.bind)

    # return a list of the column names (sample names)
    return jsonify(list(df.columns)[2:])

# metadata route
@app.route("/metadata/<sample>")
def sample_metadata(sample):
    """Return the MetaData for a given sample."""
    sel = [
        Samples_Metadata.sample,
        Samples_Metadata.ETHNICITY,
        Samples_Metadata.GENDER,
        Samples_Metadata.AGE,
        Samples_Metadata.LOCATION,
        Samples_Metadata.BBTYPE,
        Samples_Metadata.WFREQ,
    ]

    results = db.session.query(*sel).filter(Samples_Metadata.sample == sample).all()

    # create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata["sample"] = result[0]
        sample_metadata["ETHNICITY"] = result[1]
        sample_metadata["GENDER"] = result[2]
        sample_metadata["AGE"] = result[3]
        sample_metadata["LOCATION"] = result[4]
        sample_metadata["BBTYPE"] = result[5]
        sample_metadata["WFREQ"] = result[6]

    print(sample_metadata)
    return jsonify(sample_metadata)

@app.route("/samples/<sample>")
def samples(sample):
    """Return `otu_ids`, `otu_labels`,and `sample_values`."""
    stmt = db.session.query(Samples).statement
    df = pd.read_sql_query(stmt, db.session.bind)

    # filter the data based on the sample number and only keep rows with values above 1
    sample_data = df.loc[df[sample] > 1, ["otu_id", "otu_label", sample]]

    # sort by sample
    sample_data.sort_values(by=sample, ascending=False, inplace=True)

    # format the data to send as json
    data = {
        "otu_ids": sample_data.otu_id.values.tolist(),
        "sample_values": sample_data[sample].values.tolist(),
        "otu_labels": sample_data.otu_label.tolist(),
    }
    return jsonify(data)

# run app
if __name__ == "__main__":
    app.run()
