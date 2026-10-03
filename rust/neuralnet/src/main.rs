mod neuralnetwork;

use neuralnetwork::NeuralNetwork;
use std::env;
use std::error::Error;
use std::fs::File;
use std::io::{BufReader, prelude::*};


fn parse_row(line: &str) -> ([f64; 2], f64) {
    let v: Vec<f64> = line
        .split(',')
        .map(|x| x.trim().parse::<f64>())
        .collect::<Result<_, _>>()
        .expect("failed to parse row as f64 values");
    ([v[0], v[1]], v[2])
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();
    let filename = args.get(1).ok_or("Missing data file")?;

    let file = File::open(filename)?;
    let reader = BufReader::new(file);
    let (input, output): (Vec<[f64; 2]>, Vec<f64>) = reader.lines()
	.map(|line| parse_row(&line.expect("failed to read line")))
	.unzip();

    let mut nn = NeuralNetwork::new();
    println!("{}", nn);
    nn.train(&input, &output, 10000, 0.1);
    println!("{}", nn.predict(&[0.23, 0.56]));
    println!("{}", nn.predict(&[0.98, 0.88]));
    Ok(())
}
