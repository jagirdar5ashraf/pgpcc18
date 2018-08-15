using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using WingTipToysEntities;

namespace WingTipToysDemo.Controllers
{
    public interface IWingTipToyService
    {
        Task<IEnumerable<ToyDetailsViewModel>> GetToyList ();
    }

    public class WingTipToyService : IWingTipToyService
    {
        private readonly HttpClient httpClient = new HttpClient ();

        private HttpRequestMessage httpReqMsg = new HttpRequestMessage ();


        public async Task<IEnumerable<ToyDetailsViewModel>> GetToyList ()
        {
            httpReqMsg.RequestUri = new Uri("https://wingtiptoysapi-ashraf.azurewebsites.net/api/ToyDetails");
            var response = await httpClient.SendAsync(httpReqMsg);
            return await response.Content.ReadAsAsync<IEnumerable<ToyDetailsViewModel>>();
        }
    }
}