// https://dev.to/farshed/building-a-neural-network-in-rust-from-scratch-5bm1

use std::fmt;
use rand::RngExt;

pub struct NeuralNetwork {
    weights: Vec<f64>,
    bias: f64,
}

impl fmt::Display for NeuralNetwork {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "NeuralNetwork {:?} {}", self.weights, self.bias)
    }
}

impl NeuralNetwork {
    pub fn new() -> NeuralNetwork  {
        /*
         x1*w1 -
                |--(z)-- f(x) -> a
         x2*w2 -    |
                    |
             b -----

         z = x1*w1 + x2*w2 + b
         a = f(z), where f = activation function (e.g. sigmoid, ReLU)
        */
        let mut rng = rand::rng();
        NeuralNetwork {
            weights: vec![rng.random(), rng.random()],
            bias: rng.random(),
        }
    }

    /// Activation function
    fn sigmoid(x: f64) -> f64 {
        1.0 / (1.0 + (-x).exp())
    }

    /// Returns the derivative of sigmoid(x)
    ///
    /// # Arguments
    ///
    /// * `s` The value of sigmoid(x) which should have already been computed
    ///
    fn derivative_sigmoid(s: f64) -> f64 {
        s * (1.0 - s)
    }

    pub fn predict(&self, input: &[f64]) -> f64 {
        Self::sigmoid(self.bias + self.weights.iter()
            .zip(input.iter())
            .map(|(w, i)| w * i)
            .sum::<f64>())
    }

    pub fn train<R: AsRef<[f64]>>(&mut self, inputs: &[R], outputs: &[f64], epochs: u32, learning_rate: f64) {
        for _ in 0..epochs {
            for (i, input) in inputs.iter().enumerate() {
                let input = input.as_ref();

                let prediction = self.predict(input);
                let error = outputs[i] - prediction;
                let delta = Self::derivative_sigmoid(prediction);
                let gradient = error * delta;

                // Backpropagation. Move weights in the direction that reduces error.
                for iter in self.weights.iter_mut().zip(input.iter()) {
                    let (weight, input) = iter;
                    *weight += learning_rate * gradient * (*input);
                }
                self.bias += learning_rate * gradient;
            }
        }
    }
}
