import matplotlib.pyplot as plt


class Mixin:

    def plot_diagram_profiles(self, port_type:str='electric', names:list=None):
        """
        print the profiles in a diagram
        :param names:   specify the names, default=None: plot all
        """
        if names is None:
            names = self.names
        plt.figure()
        for name in names:
            if name in self.names:
                if port_type in self.components[name].ports:
                    data = [x[port_type] for x in self.components[name].ports_history]
                    plt.plot(data, linewidth=1, label=name)

        plt.xlabel("Zeitschritte")
        plt.ylabel("Leistung [kWh]")
        plt.legend(loc='lower right')
        plt.show()


if __name__ == '__main__':

    # Mixin.plot_diagram_profiles(None, ['1', '2'])

    daten = [4, 7, 1, 9, 5, 2, 8]
    daten2 = [2 * x for x in daten]
    plt.plot(daten, label='d')
    plt.plot(daten2, label='44')
    plt.xlabel("Zeitschritte")
    plt.ylabel("Leistung [kW]")
    plt.legend(loc='lower right')
    plt.show()