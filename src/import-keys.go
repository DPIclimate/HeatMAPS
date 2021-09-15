package main

import (
	"log"
	"os"
	"strings"
	"github.com/joho/godotenv"
)


func GetEnvVariable(key string) string {
	err := godotenv.Load(".env")

	if err != nil {
		log.Fatalf("Error loading .env file")
	}

	return os.Getenv(key)
}


func GetEnvVariables() map[string]string{

	evs, err := godotenv.Read()

	if err != nil {
		log.Fatal(err)
	}

	return evs 
}


func GetThingSpeakCredentials() (map[string]string, map[string]string) {
	
	evs := GetEnvVariables()

	var ids = make(map[string]string)
	var keys = make(map[string]string)

	for index, value := range evs{
		res := strings.Contains(index, "ID")
		if res {
			ids[index] = value
		}
		res = strings.Contains(index, "KEY")
		if res {
			keys[index] = value
		}
	}

	return ids, keys
}
