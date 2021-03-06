import pandas as pd
import numpy as np
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import os
import glob

from urllib.parse import urlparse, urljoin

import click

from pandas.io.json import json_normalize
import json
import ast

from flatten_json import flatten

def get_request(pure_url, api_key, version, resource, params = {}):
	headers = {
		"Accept": "application/json",
		"api-key": api_key
	}

	url = urljoin(pure_url, "/ws/api/{}/{}".format(version,resource)) 

	try:
		return requests.get(url, params = params, headers = headers, verify=False)
	except requests.ConnectionError:
		print("Request error! {0} ({1})".format(url,params))
		return None	


def get_site(url):
	return urlparse(url).netloc.replace(".","_")

def get_excel_path(site):
	return os.path.join(site, "{}.xlsx".format(site))

def fetch_data(url, api_key, version, family = "research-outputs", fields = "uuid,title.value,info.*", resume=False, flatten_data = True):

	current = 0
	size = 50
	total = np.inf

	site = get_site(url)

	if resume:
		click.echo("Resuming...")
		getnum = lambda x: int(x.split("/")[-1].split(".")[0])
		csv_files = glob.glob(os.path.join(site, "*.csv"))
		if csv_files:
			pages = sorted(list(map(getnum, csv_files)))
			current = pages[-1]

	bar = None

	while current < total:
		pars = {
			"fields": fields,
			"size": size,
			"offset": current
		}

		dataset = get_request(url, api_key, version, family, pars).json()

		total = dataset['count'] 
		
		if bar is None:
			bar = click.progressbar(length=total, label="Downloading data:", show_eta=True)

			click.echo("Found {} records.".format(total))

			if current > 0:
				bar.update(current)

			if current >= total:
				break

		current = current + size
		bar.update(size)

		df = pd.DataFrame()
		if flatten_data:
			df = pd.concat([pd.DataFrame.from_dict(flatten(d), orient='index').transpose() for d in dataset["items"]]).set_index("uuid")

			df_unflattened = pd.json_normalize(data=dataset["items"], sep='_')
			df_unflattened.set_index("uuid", inplace=True)
			extra_columns = list(set(df_unflattened.columns).difference(set(df.columns)))

			df = df.join(df_unflattened.loc[:, df_unflattened.columns.isin(extra_columns)])
		else:
			df = pd.json_normalize(data=dataset['items'])
			df.set_index("uuid", inplace=True)

		if not os.path.exists(site):
			os.mkdir(site)

		df.to_csv(os.path.join(site,"{}.csv".format(current)))
		
	csv_files = glob.glob(os.path.join(site, "*.csv"))

	result = pd.DataFrame()
	with click.progressbar(csv_files, label="Combining dataset...", show_eta=True) as bar:
		for csv_file in bar:
			result = pd.concat([result, pd.read_csv(csv_file, index_col="uuid")])

	output_filename = get_excel_path(site)

	click.echo("Saving output as {}...".format(output_filename))
	result.to_excel(output_filename)

# Utility function to flatten JSON and combine
def get_split_df(df, id_column, target_column):

	# if the column doesn't exist, set it to null
	if target_column not in df.columns:
		df[target_column] = None

	isnull = df[target_column].isnull()
	result = pd.DataFrame()
	for idx, row in df.loc[~isnull,:].iterrows():
		new_df = pd.json_normalize(ast.literal_eval(row[target_column]))
		new_df[id_column] = row[id_column]
		new_df.set_index(id_column, inplace=True)
		result = pd.concat([result,new_df])
	return result

@click.command()
@click.argument("url")
@click.argument("apikey")
@click.option("--apiversion", help = "The API version to use. Default: '522'.", default = "522")
@click.option("--family", help = "The family to download.", default = "research-outputs")
@click.option("--fields", help = "The fields to retrieve.", default = "uuid,title.value,info.additionalExternalIds.*")
@click.option("--resume", help = "Resume harvesting from last time.", default = False, is_flag=True)
@click.option("--flatten_data", help="Flattens nested data into separate columns.", default=True)
def main(url, apikey, apiversion, family, fields, resume, flatten_data):

	click.echo("Connecting to {}.".format(url))

	data = fetch_data(url, apikey, apiversion, family, fields, resume, flatten_data)

main()
