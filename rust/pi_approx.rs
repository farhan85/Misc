use clap::{Arg, App, value_t_or_exit};

fn leibniz_formula(n: u32) -> f64 {
    let mut val: f64 = 1.0;
    let mut curr_denominator: f64 = 1.0;
    let mut odd: bool = true;
    for _ in 0..n {
        curr_denominator += 2.0;
        let sign = match odd { true => -1.0, false => 1.0 };
        odd = !odd;
        val += sign / curr_denominator;
    }
    val * 4.0
}

fn vietes_formula(n: u32) -> f64 {
    let mut numerator: f64 = 1.0;
    let mut curr_numerator: f64 = 0.0;
    for _ in 0..n {
        curr_numerator = (2.0 + curr_numerator).sqrt();
        numerator *= curr_numerator;
    }
    2.0 / (numerator / f64::powf(2.0, n as f64))
}

fn bailey_borwein_plouffe_formula(max_n: u32) -> f64 {
    let mut val = 0.0;
    for n in 0..max_n {
        let n8: f64 = n as f64 * 8.0;
        let mut nth_term: f64 = 0.0;
        nth_term += 4.0 / (n8 + 1.0);
        nth_term -= 2.0 / (n8 + 4.0);
        nth_term -= 1.0 / (n8 + 5.0);
        nth_term -= 1.0 / (n8 + 6.0);
        nth_term /= f64::powf(16.0, n as f64);
        val += nth_term;
    }
    val
}

fn bellards_formula(max_n: u32) -> f64 {
    let mut val = 0.0;
    for n in 0..max_n {
        let n4: f64 = n as f64 * 4.0;
        let n10: f64 = n as f64 * 10.0;
        let sign = match n % 2 == 0 { true => 1.0, false => -1.0 };
        let mut nth_term: f64 = 0.0;
        nth_term -= 32.0 / (n4 + 1.0);
        nth_term -= 1.0 / (n4 + 3.0);
        nth_term += 256.0 / (n10 + 1.0);
        nth_term -= 64.0 / (n10 + 3.0);
        nth_term -= 4.0 / (n10 + 5.0);
        nth_term -= 4.0 / (n10 + 7.0);
        nth_term += 1.0 / (n10 + 9.0);
        nth_term *= sign / f64::powf(2.0, n10);
        val += nth_term;
    }
    val / 64.0
}

fn borweins_algorithm(max_n: u32) -> f64 {
    let mut y: f64 = f64::sqrt(2.0) - 1.0;
    let mut a: f64 = 2.0*y*y;
    let mut tmp: f64;
    for n in 0..max_n {
        tmp = f64::powf(1.0 - y*y*y*y, 0.25);
        y = (1.0 - tmp)/(1.0 + tmp);
        a = a*f64::powf(1.0 + y, 4.0) - f64::powf(2.0, 2.0*(n as f64) + 3.0)*y*(1.0 + y + y*y);
    }
    1.0 / a
}

fn main() {
    let matches = App::new("PI Calculator")
            .about("Uses various methods to compute PI")
            .arg(Arg::with_name("num_iterations")
               .short("i")
               .long("iterations")
               .value_name("NUM")
               .help("Number of iterations to use")
               .takes_value(true))
            .get_matches();

    let num_iterations = value_t_or_exit!(matches.value_of("num_iterations"), u32);

    println!("Approximations of PI:");
    println!("Leibniz Formula                {:.50}", leibniz_formula(num_iterations));
    println!("Viète's Formula:               {:.50}", vietes_formula(num_iterations));
    println!("Bailey-Borwein-Plouffe Formula {:.50}", bailey_borwein_plouffe_formula(num_iterations));
    println!("Bellard's Formula:             {:.50}", bellards_formula(num_iterations));
    println!("Borwein's Algorithm            {:.50}", borweins_algorithm(num_iterations));
    println!("First 51 digits:               3.14159265358979323846264338327950288419716939937510");
}

