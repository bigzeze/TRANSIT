import TRANSIT

if __name__ == '__main__':
    transit = TRANSIT()
    transit.parse_args()
    transit.check_paths()
    transit.apply_simulation()

    



    myconfig = SimulationConfig()
    gridNumber = 5
    detectorNumber = 1
    laneLength = 300
    myconfig.setNetworkConfig(True,gridNumber,laneLength,1)
    myconfig.setDetectorConfig(60,'center',detector_number=detectorNumber)
    myconfig.setFlowConfig(0.2,0.5,0.4)
    myconfig.setSimulationTime(0,14400)

    num_ES = 1
    #num_VS = 3
    num_TLF = 0

    net = get_crossing_name(gridNumber)

    inject_edges_ES = [random_edge(net) for i in range(num_ES)] # EdgeSlow positions
    #inject_edges_VS = [random_edge(net) for i in range(num_VS)] # VehicleStop positions
    inject_crossings_TLF = [random_crossing(net) for i in range(num_TLF)] # TLFailure positions
    if mode == 'observe':
        print('inject area: '+ ' '.join(inject_edges_ES) + ' ' + ' '.join(inject_crossings_TLF))


    start_time = 3600
    end_time = 7200