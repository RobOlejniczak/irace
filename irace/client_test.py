"""Command line test to confirm the stats client works as expected."""


from getpass import getpass

from .stats import Client


def main():
    """Command line test for the stats client."""

    username = input("iRacing username: ")
    Client.login(username, getpass())

    for key, value in Client.cache.items():
        if value:
            print("client.cache[\"{}\"] has {:,d} keys".format(
                key,
                len(value),
            ))
        else:
            print("client.cache[\"{}\"] does not exist".format(key))

    cars = Client.cars_driven()
    print("cars: {!r}".format(cars))
    for car in cars:
        print("car: {} personal_best: {}".format(
            car,
            Client.personal_best(car_id=car)
        ))


if __name__ == "__main__":
    main()
