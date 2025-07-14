package com.pyxos;

import javax.sql.DataSource;
import java.sql.ResultSet;
import java.sql.SQLException;

public class Test {

    public static void main(String[] args) throws SQLException {
        DataSource dataSource = Database.createConnectionPool();

        ResultSet rs =
                dataSource.getConnection().prepareStatement("select * from birds").executeQuery();

        while (rs.next()) {
            System.out
                    .println("name: " + rs.getString("bird") + " description:" + rs.getString("description"));
        }
    }
}
