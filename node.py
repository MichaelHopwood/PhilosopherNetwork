class Node:

    def __init__(self, name, page="NA", birthyear='NA', birthlong='NA', birthlat='NA'):
        self.name = name
        self.page = page
        self.birth = birthyear
        self.birthlong = birthlong
        self.birthlat = birthlat
        self.incoming_link_names = []  # this is a list of the names of incoming nodes
        self.incoming_links = []       # this is a list of references to incoming nodes
        self.outgoing_link_names = []  # this is a list of the names of outgoing nodes
        self.outgoing_links = []       # this is a list of references to outgoing nodes
        self.k_in = 0
        self.k_out = 0

    def add_influence(self, i_name, i_page):
        self.incoming_link_names.append(i_name)
        self.incoming_links.append(i_page)

    def add_influenced(self, i_name, i_page):
        self.outgoing_link_names.append(i_name)
        self.outgoing_links.append(i_page)

    def get_incoming(self):
        """
        Returns a list of tuples, each of which contains the name and wiki page of an incoming link
        :return: list of tuples
        """
        return [(name, page) for (name, page) in zip(self.incoming_link_names, self.incoming_links)]

    def get_outgoing(self):
        """
        Returns a list of tuples, each of which contains the name and wiki page of an outgoing link
        :return: list of tuples
        """
        return [(name, page) for (name, page) in zip(self.outgoing_link_names, self.outgoing_links)]

    def get_name(self):
        return self.name

    def get_page(self):
        return self.page

    def set_page(self, page):
        self.page = page

    def get_birth(self):
        return self.birth

    def set_birth(self, birth):
        self.birth = birth

    def deduplicate_links(self):
        self.incoming_link_names = set(self.incoming_link_names)
        self.outgoing_link_names = set(self.outgoing_link_names)
        self.incoming_links = set(self.incoming_links)
        self.outgoing_links = set(self.outgoing_links)

    def summary(self):
        print(f"\nThe philosopher {self.name} was influenced by:")
        for i in self.incoming_link_names:
            print(i)
        print(f"\nThe philosopher {self.name} influenced:")
        for i in self.outgoing_link_names:
            print(i)

    def brief_summary(self):
        print(f"Philosopher {self.name} with life {self.birth} has {len(self.incoming_links)} influences and influenced {len(self.outgoing_links)}")

    def fetch_data(self):
        incoming_links = ""
        outgoing_links = ""
        for link in self.incoming_link_names:
            incoming_links += link+":"
        for link in self.outgoing_link_names:
            outgoing_links += link+":"

        return self.name, self.birth, incoming_links, outgoing_links

