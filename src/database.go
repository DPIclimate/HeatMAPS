package main

import (
	"fmt"
	"log"
	"time"
	"database/sql"
	_ "github.com/go-sql-driver/mysql"
)


func SqlConnect() *sql.DB {
	fmt.Print("Connecting to DB... ")

	// username:password@tcp(address:port)/database
	db, err := sql.Open("mysql", "admin:admin@tcp(127.0.0.1:33060)/iot-spatial-interpolation")

	if err != nil{
		log.Fatal(err)
	}

	fmt.Println("Success.")

	db.SetConnMaxLifetime(time.Minute * 3) // Timeout. Ensures conns close safely.
	db.SetMaxOpenConns(5)
	db.SetMaxIdleConns(5)

	return db
}


func CreateAccessTable(db *sql.DB) {

	createTable, err := db.Query("CREATE TABLE IF NOT EXISTS access (name text, access_id text, access_key text)")

	if err != nil {
		log.Fatal(err)
	}

	defer createTable.Close()

	fmt.Println("[Created]: Access table")
}


func PopulateAccessTable(db *sql.DB) {
	
	var nRows int
	err := db.QueryRow("SELECT COUNT(*) FROM access").Scan(&nRows)

	if err != nil{
		log.Fatal(err)
	}

	fmt.Println(nRows)

}
