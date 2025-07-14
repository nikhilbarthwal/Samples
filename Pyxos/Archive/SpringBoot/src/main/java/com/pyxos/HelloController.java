package com.pyxos;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;

@RestController
public class HelloController {
    
    @RequestMapping("/")
    public String index() {
        return "Hello! This is the Pyxos service on Google Cloud Platform\n";
    }

    @GetMapping("/user/{id}")
    public ResponseEntity<String> handleRequest(@PathVariable("id") String id) {

        if (id.endsWith("nikhil"))
            return ResponseEntity.status(200).body("Received id: " + id + " is Nikhil");
        return ResponseEntity.status(403).body("Received id: " + id + " is not Nikhil");
    }
}
