using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using WingTipToysEntities;

namespace WingTipToysDemo.Controllers
{
    public class WingTipToyService : IWingTipToyService
    {
        private readonly HttpClient httpClient = new HttpClient();

        private HttpRequestMessage httpReqMsg = new HttpRequestMessage();


        public async Task<IEnumerable<ToyDetailsViewModel>> GetToyList ( )
        {
            // From storage directly    
            //httpReqMsg.RequestUri = new Uri("https://wingtiptoysapi-ashraf.azurewebsites.net/api/ToyDetails");

            // From CDN endpoint
            httpReqMsg.RequestUri = new Uri("https://wingtiptoysapi-fromcdn.azurewebsites.net/api/ToyDetails");
            var response = await httpClient.SendAsync(httpReqMsg);
            return await response.Content.ReadAsAsync<IEnumerable<ToyDetailsViewModel>>();
            //throw new System.NotImplementedException();
        }
    }
}