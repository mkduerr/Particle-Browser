# Particle Browser
Interactive visualization of particles collected on substrate using processed scanning electron microscopy images.


Prototype developed for product control in a project to provide synthetic particles on substrates.

## Application Scenario

Substrate specimens were generated within a quality controlled process. The final product ready to be shipped to the customer was characterized by scanning the substrate surface with an electron microscope. The obtained imaging data is processed and an interactive visualization is generated which allows easy inspection by the customer. The interactivity empowers the customer to verify the quality with his own means without the need to undertake extensive efforts.

## Data Processing & Generating the Visualization

* The python script [process_PAsearch.py](process_PAsearch.py) processes the raw data of a given substrate.

* The raw data is in a directory, like the directory [DemoData](/DemoData).

* The python script [PA_GeneratePage](PA_GeneratePage.py) generates a webpage with three interactive plots as shown in Figure 1.

## Interactive Visualization

The interactive visualization looks like this:

Each particle is visualized by a dot. The dot-size is proportional to the
diameter of the particle. The color indicates with the uranium content.

A box or lasso selection tool allows to select a group of particles by their properties *location on substrate* or *particle diameter* and *circularity*.


## Authors

* **Ronal Middendorp**
* **Martin Dürr**

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details


<br />Image Data is licensed under a <a rel="license"
href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img
alt="Creative Commons License" style="border-width:0"
src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a>
