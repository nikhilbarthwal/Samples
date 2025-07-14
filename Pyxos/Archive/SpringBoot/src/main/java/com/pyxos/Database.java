package com.pyxos;

import javax.sql.DataSource;
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import java.sql.ResultSet;
import java.sql.SQLException;


public class Database {
    private static final String INSTANCE_CONNECTION_NAME =
            "pyx-format:us-west1:database";
    private static final String DB_USER = "nikhil";
    private static final String DB_PASS = "nikhil12";
    private static final String DB_NAME = "database";

    public static DataSource createConnectionPool() {
        // create a new configuration and set the database credentials
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(String.format("jdbc:postgresql:///%s", DB_NAME));
        config.setUsername(DB_USER);
        config.setPassword(DB_PASS);
        config.addDataSourceProperty("socketFactory", "com.google.cloud.sql.postgres.SocketFactory");
        config.addDataSourceProperty("cloudSqlInstance", INSTANCE_CONNECTION_NAME);

        // Initialize the connection pool using the configuration object.
        return new HikariDataSource(config);
    }
}
