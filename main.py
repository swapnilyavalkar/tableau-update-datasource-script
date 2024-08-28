import pandas as pd
import psycopg2
import tableauserverclient as TSC
import config

SERVER_URL = 'https://abc.com/'
TS_USER_NAME = ''
TS_PASSWORD = ''
SITE_NAME = ''

df_processed_ds = pd.DataFrame(
    columns=['site_name', 'url_namespace', 'projects_name', 'datasources_name', 'data_connections_name',
             'db_server_name', 'db_port', 'db_username', 'db_password', 'db_authentication', 'has_extract',
             'data_connections_luid', 'datasources_luid', 'dbclass'])

if __name__ == '__main__':
    try:
        print('Connecting to PG SQL Database.')
        paramspg = config.configpg()
        PGSQL_CONNECTION = psycopg2.connect(**paramspg)
        cursor = PGSQL_CONNECTION.cursor()
        print('PG SQL Database Cursor created successfully.')
        print('Reading PG SQL Query.')
        query = open('sql-query.sql', 'r')
        final_query = query.read()
        print('Executing PG SQL Query : ' + final_query)
        data = pd.read_sql_query(final_query, PGSQL_CONNECTION)
        df_ds_data = pd.DataFrame(data)
        df_ds_data.to_excel("data-all-ds.xlsx", sheet_name="data", index=False)

        tableau_auth = TSC.TableauAuth(TS_USER_NAME, TS_PASSWORD)
        server = TSC.Server(SERVER_URL, use_server_version=True)
        server.add_http_options({'verify': False})
        with server.auth.sign_in(tableau_auth):
            all_sites = list(TSC.Pager(server.sites))
            for site in all_sites:
                for index, row in df_ds_data.iterrows():
                    if site.name == row['site_name']:
                        server.auth.switch_site(site)
                        # get the data source
                        datasource = server.datasources.get_by_id(row['datasources_luid'])
                        # get the connection information
                        server.datasources.populate_connections(datasource)
                        # print the information about the first connection item
                        connection = datasource.connections[0]
                        if connection.connection_type == 'oracle' and connection.server_address == '123.abc.com':
                            #update required db name in below varible
                            connection.server_address = "456.abc.com"

                            # call the update method with the data source item
                            updated_datasource = server.datasources.update_connection(datasource, connection)
                            print('updated connection :', connection)

                            df_processed_ds = df_processed_ds.append({
                                'site_name': row['site_name'],
                                'url_namespace': row['url_namespace'],
                                'projects_name': row['projects_name'],
                                'datasources_name': row['datasources_name'],
                                'data_connections_name': row['data_connections_name'],
                                'db_server_name': row['db_server_name'],
                                'db_port': row['db_port'],
                                'db_username': row['db_username'],
                                'db_password': row['db_password'],
                                'db_authentication': row['db_authentication'],
                                'has_extract': row['has_extract'],
                                'data_connections_luid': row['data_connections_luid'],
                                'datasources_luid': row['datasources_luid'],
                                'dbclass': row['dbclass'],
                                'updated_connection_id': connection.id,
                                'db_server_old_name': row['db_server_name'],
                                'db_server_new_name': connection.server_address,
                            }, ignore_index=True)
        df_processed_ds.to_excel("df_processed_ds.xlsx", sheet_name="data", index=False)
    except Exception as e:
        print("Exception Occurred In: PGsignIn", exc_info=True)
print("All data sources updated.")