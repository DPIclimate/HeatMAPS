package main

import (
	_ "fmt"
	_ "log"
)



func main() {
	db := SqlConnect()

	CreateAccessTable(db)
	GetThingSpeakCredentials()
	
//	PopulateAccessTable(db)

}

